"""
Sample prompts for testing LLM service.
"""

# Basic diagram prompts
SIMPLE_FLOWCHART_PROMPT = "Create a simple flowchart with start, process, and end nodes"

BASIC_DIAGRAM_PROMPT = "Create a basic diagram with two connected boxes"

COMPLEX_FLOWCHART_PROMPT = """Create a flowchart for a user registration process:
1. User enters email and password
2. System validates email format
3. If invalid, show error message
4. If valid, check if email already exists
5. If exists, show error message
6. If new, create account and send confirmation email
7. Show success message"""

# AWS-specific prompts
AWS_SIMPLE_PROMPT = "Create an AWS architecture diagram with EC2 and RDS"

AWS_ARCHITECTURE_PROMPT = """Create a comprehensive AWS web application architecture diagram showing:
- Route 53 for DNS
- CloudFront CDN
- Application Load Balancer
- Auto Scaling Group with EC2 instances
- RDS Multi-AZ database
- ElastiCache for caching
- S3 bucket for static assets
- VPC with public and private subnets
- NAT Gateway for outbound connectivity"""

AWS_COMPLEX_PROMPT = """Create an AWS architecture diagram showing:
- VPC with public and private subnets
- Application Load Balancer in public subnet
- EC2 instances in private subnet
- RDS database in private subnet
- NAT Gateway for outbound internet access
- S3 bucket for static assets"""

AWS_SERVERLESS_PROMPT = """Create a serverless AWS architecture with:
- API Gateway
- Lambda functions
- DynamoDB database
- S3 bucket for file storage
- CloudFront distribution"""

# System architecture prompts
MICROSERVICES_PROMPT = """Create a microservices architecture diagram showing:
- API Gateway
- User Service
- Order Service
- Payment Service
- Notification Service
- Database for each service
- Message queue between services"""

DATABASE_SCHEMA_PROMPT = """Create a database schema diagram for an e-commerce system:
- Users table
- Products table
- Orders table
- Order_Items table
- Categories table
Show relationships between tables"""

NETWORK_DIAGRAM_PROMPT = """Create a network diagram showing:
- Internet connection
- Router
- Firewall
- Switch
- Multiple workstations
- Server
- Printer"""

# Organization charts
ORG_CHART_PROMPT = """Create an organizational chart for a tech company:
- CEO at the top
- CTO and CFO reporting to CEO
- Engineering Manager and Product Manager under CTO
- Software Engineers under Engineering Manager
- Finance team under CFO"""

# Process diagrams
BUSINESS_PROCESS_PROMPT = """Create a business process diagram for order fulfillment:
1. Customer places order
2. Payment processing
3. Inventory check
4. If out of stock, backorder
5. If in stock, pick and pack
6. Ship order
7. Send tracking information
8. Delivery confirmation"""

# Edge cases and error testing prompts
EMPTY_PROMPT = ""

VERY_LONG_PROMPT = "Create a diagram " + "with many elements " * 100

SPECIAL_CHARACTERS_PROMPT = "Create a diagram with special characters: áéíóú, 中文, русский, العربية, 🚀"

AMBIGUOUS_PROMPT = "Create something"

IMPOSSIBLE_PROMPT = "Create a diagram that shows the color of sound and the weight of happiness"

# Prompts for cache testing (identical prompts)
CACHE_TEST_PROMPT_1 = "Create a simple flowchart with three steps"
CACHE_TEST_PROMPT_2 = "Create a simple flowchart with three steps"  # Identical to test cache hit

# Prompts with slight variations (for cache miss testing)
CACHE_VARIATION_PROMPT_1 = "Create a simple flowchart with three steps"
CACHE_VARIATION_PROMPT_2 = "Create a simple flowchart with three steps."  # Added period

# Prompts for different diagram types
UML_CLASS_DIAGRAM_PROMPT = """Create a UML class diagram for a library management system:
- Book class with title, author, ISBN properties
- Member class with name, ID, email properties
- Loan class connecting Book and Member
- Library class managing books and members"""

SEQUENCE_DIAGRAM_PROMPT = """Create a sequence diagram for user authentication:
- User submits login form
- Frontend validates input
- Frontend sends request to backend
- Backend checks credentials in database
- Database returns result
- Backend sends response to frontend
- Frontend redirects user or shows error"""

ENTITY_RELATIONSHIP_PROMPT = """Create an entity-relationship diagram for a blog system:
- User entity (id, username, email)
- Post entity (id, title, content, created_at)
- Comment entity (id, content, created_at)
- Category entity (id, name)
- Relationships: User has many Posts, Post has many Comments, Post belongs to Category"""