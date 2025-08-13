# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Development Server
- `npm run dev` - Start both frontend (port 3000) and backend (port 3001) in development mode
- `npm run dev:backend` - Start backend only
- `npm run dev:frontend` - Start frontend only

### Building
- `npm run build` - Build both packages for development
- `npm run build:production` - Production build with optimizations
- `npm run build:backend` - Build backend only
- `npm run build:frontend` - Build frontend only

### Testing and Validation
- `npm run test` - Run tests across all workspaces
- `npm run test:coverage` - Run tests with coverage reports
- `npm run lint` - Run ESLint across all workspaces
- `npm run lint:fix` - Auto-fix linting issues
- `npm run typecheck` - TypeScript type checking
- `npm run validate` - Run typecheck, lint, and test together (recommended before commits)

### Production
- `npm run start:production` - Start production servers
- `npm run clean` - Clean build artifacts

## Project Architecture

This is a TypeScript monorepo using npm workspaces with two main packages:

### Backend (`packages/backend/`)
- **Framework**: Express.js with TypeScript
- **AI Integration**: Anthropic Claude via `@anthropic-ai/sdk`
- **Core Services**:
  - `llmService.ts` - Claude LLM integration with caching and error handling
  - `fileService.ts` - File management for .drawio files
  - `imageService.ts` - PNG image generation using Draw.io CLI
- **API Structure**: RESTful API with main endpoint `/api/generate-diagram`
- **Error Handling**: Comprehensive error types and user-friendly messages
- **Performance**: Response caching, rate limiting, memory monitoring

### Frontend (`packages/frontend/`)
- **Framework**: Next.js 14 with App Router
- **Components**:
  - `MainPage.tsx` - Main application container
  - `InputForm.tsx` - Natural language input interface
  - `ResultDisplay.tsx` - Generated diagram preview and download
  - `ErrorMessage.tsx` - User-friendly error display
  - `ConnectionStatus.tsx` - Network status monitoring
- **Features**: Network status detection, retry mechanisms, optimized image loading

### Key Dependencies
- **Backend**: `@anthropic-ai/sdk`, `express`, `zod` (validation), `uuid`
- **Frontend**: `next`, `react`, TypeScript
- **Development**: `tsx` (backend dev server), `jest` (testing), `eslint`

## Environment Setup

### Required Environment Variables
- `ANTHROPIC_API_KEY` - Claude API key (backend)
- `NEXT_PUBLIC_API_URL` - Backend API URL (frontend)
- `FRONTEND_URL` - Frontend URL (backend CORS)

### External Dependencies
- **Draw.io CLI**: Required for PNG image generation
  - Install: `npm install -g @drawio/drawio-desktop-cli`
  - Used by `imageService.ts` to convert XML to PNG

## Development Workflow

1. **Setup**: Run `npm install` then `npm install --workspaces`
2. **Environment**: Copy `.env.example` files and configure API keys
3. **Development**: Use `npm run dev` to start both servers
4. **Testing**: Run `npm run validate` before committing changes
5. **Docker**: Use `docker-compose.yml` for containerized development

## Code Patterns

### Error Handling
- Use `LLMError` class with specific error codes (`LLMErrorCode`)
- Frontend uses `ErrorHandler` utility for consistent error processing
- All errors should provide user-friendly messages and retry guidance

### File Management
- Temporary files use UUID naming in `temp/` directory
- Automatic cleanup of old files
- Secure file serving with temporary URLs

### API Design
- RESTful endpoints with consistent response structure
- Zod schemas for request validation
- Comprehensive error responses with status codes

## Testing Strategy

- **Unit Tests**: Individual service and component testing
- **Integration Tests**: End-to-end API workflow testing
- **E2E Tests**: Full user journey testing
- Test files located in `__tests__/` directories within each package