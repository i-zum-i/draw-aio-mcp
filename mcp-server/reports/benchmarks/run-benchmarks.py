#!/usr/bin/env python3
"""
Performance benchmark script for MCP Server
Measures response times, throughput, and resource utilization
"""

import asyncio
import time
import json
import statistics
import psutil
import docker
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import aiohttp
import subprocess

@dataclass
class BenchmarkResult:
    operation: str
    response_times: List[float]
    success_count: int
    error_count: int
    start_time: float
    end_time: float

class MCPServerBenchmark:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.docker_client = docker.from_env()
        self.results: List[BenchmarkResult] = []
        
    async def benchmark_xml_generation(self, prompts: List[str], iterations: int = 10) -> BenchmarkResult:
        """Benchmark XML generation performance"""
        response_times = []
        success_count = 0
        error_count = 0
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            for i in range(iterations):
                prompt = prompts[i % len(prompts)]
                
                try:
                    request_start = time.time()
                    
                    # Simulate MCP tool call
                    payload = {
                        "method": "generate_drawio_xml",
                        "params": {"prompt": prompt}
                    }
                    
                    async with session.post(
                        f"{self.server_url}/mcp/tools/generate-drawio-xml",
                        json=payload,
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            await response.json()
                            success_count += 1
                        else:
                            error_count += 1
                    
                    response_times.append((time.time() - request_start) * 1000)
                    
                except Exception as e:
                    error_count += 1
                    print(f"Error in XML generation: {e}")
        
        end_time = time.time()
        
        return BenchmarkResult(
            operation="xml_generation",
            response_times=response_times,
            success_count=success_count,
            error_count=error_count,
            start_time=start_time,
            end_time=end_time
        )
    
    async def benchmark_file_operations(self, iterations: int = 50) -> BenchmarkResult:
        """Benchmark file save and retrieval operations"""
        response_times = []
        success_count = 0
        error_count = 0
        
        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mxfile host="app.diagrams.net">
            <diagram name="Test">
                <mxGraphModel>
                    <root>
                        <mxCell id="0"/>
                        <mxCell id="1" parent="0"/>
                        <mxCell id="2" value="Test" vertex="1" parent="1">
                            <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
                        </mxCell>
                    </root>
                </mxGraphModel>
            </diagram>
        </mxfile>"""
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            for i in range(iterations):
                try:
                    request_start = time.time()
                    
                    payload = {
                        "method": "save_drawio_file",
                        "params": {
                            "xml_content": sample_xml,
                            "filename": f"benchmark-{i}.drawio"
                        }
                    }
                    
                    async with session.post(
                        f"{self.server_url}/mcp/tools/save-drawio-file",
                        json=payload,
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            success_count += 1
                        else:
                            error_count += 1
                    
                    response_times.append((time.time() - request_start) * 1000)
                    
                except Exception as e:
                    error_count += 1
                    print(f"Error in file operation: {e}")
        
        end_time = time.time()
        
        return BenchmarkResult(
            operation="file_operations",
            response_times=response_times,
            success_count=success_count,
            error_count=error_count,
            start_time=start_time,
            end_time=end_time
        )
    
    async def benchmark_concurrent_users(self, user_counts: List[int]) -> Dict[int, BenchmarkResult]:
        """Benchmark performance under concurrent load"""
        results = {}
        
        for user_count in user_counts:
            print(f"Testing with {user_count} concurrent users...")
            
            tasks = []
            start_time = time.time()
            
            for _ in range(user_count):
                task = asyncio.create_task(self.simulate_user_session())
                tasks.append(task)
            
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            
            # Aggregate results
            all_response_times = []
            success_count = 0
            error_count = 0
            
            for result in completed_tasks:
                if isinstance(result, Exception):
                    error_count += 1
                else:
                    all_response_times.extend(result['response_times'])
                    success_count += result['success_count']
                    error_count += result['error_count']
            
            results[user_count] = BenchmarkResult(
                operation=f"concurrent_users_{user_count}",
                response_times=all_response_times,
                success_count=success_count,
                error_count=error_count,
                start_time=start_time,
                end_time=end_time
            )
        
        return results
    
    async def simulate_user_session(self) -> Dict[str, Any]:
        """Simulate a typical user session"""
        response_times = []
        success_count = 0
        error_count = 0
        
        # Typical user workflow: generate -> save -> convert
        prompts = [
            "Create a simple web application architecture",
            "Design a microservices system",
            "Show a database schema for e-commerce"
        ]
        
        async with aiohttp.ClientSession() as session:
            try:
                # Generate XML
                start = time.time()
                async with session.post(
                    f"{self.server_url}/mcp/tools/generate-drawio-xml",
                    json={"method": "generate_drawio_xml", "params": {"prompt": prompts[0]}},
                    timeout=30
                ) as response:
                    if response.status == 200:
                        xml_data = await response.json()
                        success_count += 1
                        response_times.append((time.time() - start) * 1000)
                        
                        # Save file
                        start = time.time()
                        async with session.post(
                            f"{self.server_url}/mcp/tools/save-drawio-file",
                            json={
                                "method": "save_drawio_file",
                                "params": {
                                    "xml_content": xml_data.get("xml_content", ""),
                                    "filename": "user-session.drawio"
                                }
                            },
                            timeout=10
                        ) as save_response:
                            if save_response.status == 200:
                                success_count += 1
                                response_times.append((time.time() - start) * 1000)
                            else:
                                error_count += 1
                    else:
                        error_count += 1
                        
            except Exception as e:
                error_count += 1
                print(f"Error in user session: {e}")
        
        return {
            'response_times': response_times,
            'success_count': success_count,
            'error_count': error_count
        }
    
    def get_container_stats(self, container_name: str = "mcp-server") -> Dict[str, Any]:
        """Get Docker container resource usage statistics"""
        try:
            container = self.docker_client.containers.get(container_name)
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * 100.0
            
            # Memory usage
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            return {
                'cpu_percent': cpu_percent,
                'memory_usage_mb': memory_usage / (1024 * 1024),
                'memory_limit_mb': memory_limit / (1024 * 1024),
                'memory_percent': memory_percent,
                'network_rx_bytes': stats['networks']['eth0']['rx_bytes'],
                'network_tx_bytes': stats['networks']['eth0']['tx_bytes']
            }
        except Exception as e:
            print(f"Error getting container stats: {e}")
            return {}
    
    def analyze_results(self, result: BenchmarkResult) -> Dict[str, Any]:
        """Analyze benchmark results and calculate statistics"""
        if not result.response_times:
            return {"error": "No response times recorded"}
        
        response_times = result.response_times
        total_requests = result.success_count + result.error_count
        duration = result.end_time - result.start_time
        
        return {
            'operation': result.operation,
            'total_requests': total_requests,
            'successful_requests': result.success_count,
            'failed_requests': result.error_count,
            'success_rate': (result.success_count / total_requests) * 100 if total_requests > 0 else 0,
            'duration_seconds': duration,
            'requests_per_second': total_requests / duration if duration > 0 else 0,
            'response_time_stats': {
                'min_ms': min(response_times),
                'max_ms': max(response_times),
                'avg_ms': statistics.mean(response_times),
                'median_ms': statistics.median(response_times),
                'p95_ms': self.percentile(response_times, 95),
                'p99_ms': self.percentile(response_times, 99)
            }
        }
    
    def percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of a dataset"""
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    async def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        print("Starting MCP Server Performance Benchmark...")
        
        # Test prompts
        test_prompts = [
            "Create a simple web application architecture with frontend, backend, and database",
            "Design an AWS architecture with VPC, EC2, RDS, and S3",
            "Show a microservices system with API gateway and multiple services",
            "Create a database ERD for an e-commerce system",
            "Design a network topology with routers, switches, and firewalls"
        ]
        
        results = {}
        
        # XML Generation Benchmark
        print("Running XML generation benchmark...")
        xml_result = await self.benchmark_xml_generation(test_prompts, 20)
        results['xml_generation'] = self.analyze_results(xml_result)
        
        # File Operations Benchmark
        print("Running file operations benchmark...")
        file_result = await self.benchmark_file_operations(50)
        results['file_operations'] = self.analyze_results(file_result)
        
        # Concurrent Users Benchmark
        print("Running concurrent users benchmark...")
        concurrent_results = await self.benchmark_concurrent_users([1, 5, 10, 15])
        results['concurrent_users'] = {}
        for user_count, result in concurrent_results.items():
            results['concurrent_users'][user_count] = self.analyze_results(result)
        
        # Container Stats
        print("Collecting container statistics...")
        results['container_stats'] = self.get_container_stats()
        
        # System Info
        results['system_info'] = {
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'timestamp': datetime.now().isoformat()
        }
        
        return results

async def main():
    """Main benchmark execution"""
    benchmark = MCPServerBenchmark()
    
    # Wait for server to be ready
    print("Waiting for MCP server to be ready...")
    await asyncio.sleep(5)
    
    # Run benchmarks
    results = await benchmark.run_full_benchmark()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nBenchmark completed! Results saved to {filename}")
    
    # Print summary
    print("\n=== BENCHMARK SUMMARY ===")
    for operation, data in results.items():
        if isinstance(data, dict) and 'response_time_stats' in data:
            stats = data['response_time_stats']
            print(f"\n{operation.upper()}:")
            print(f"  Success Rate: {data['success_rate']:.1f}%")
            print(f"  Avg Response: {stats['avg_ms']:.1f}ms")
            print(f"  P95 Response: {stats['p95_ms']:.1f}ms")
            print(f"  Requests/sec: {data['requests_per_second']:.1f}")

if __name__ == "__main__":
    asyncio.run(main())