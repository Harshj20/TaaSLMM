"""Main gRPC server."""

import asyncio
import signal
import sys
from concurrent import futures

import grpc
from taas_server.generated import taas_pb2_grpc
from taas_server.services import TaskServiceServicer
from taas_server.db.database import init_database
from taas_server.core import get_state_manager
from taas_server.tasks.examples import config_tasks  # Import to register tasks


class TaasServer:
    """TaaS gRPC server."""
    
    def __init__(self, host: str = "[::]", port: int = 50051, database_url: str = "sqlite:///taas.db"):
        """Initialize the server."""
        self.host = host
        self.port = port
        self.database_url = database_url
        self.server: Optional[grpc.aio.Server] = None
        
    async def start(self) -> None:
        """Start the gRPC server."""
        print("Initializing TaaS Server...")
        
        # Initialize database
        print(f"Connecting to database: {self.database_url}")
        init_database(self.database_url)
        
        # Recover state from last session
        print("Recovering state from last session...")
        state_manager = get_state_manager()
        state_manager.recover_from_last_session()
        
        # Create gRPC server
        self.server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=10)
        )
        
        # Register services
        taas_pb2_grpc.add_TaskServiceServicer_to_server(
            TaskServiceServicer(), self.server
        )
        
        # Add server port
        server_address = f"{self.host}:{self.port}"
        self.server.add_insecure_port(server_address)
        
        # Start server
        await self.server.start()
        print(f"✓ TaaS Server started on {server_address}")
        print(f"✓ Ready to accept task requests")
        
        # Wait for termination
        await self.server.wait_for_termination()
    
    async def stop(self) -> None:
        """Stop the gRPC server gracefully."""
        if self.server:
            print("\nShutting down server...")
            
            # Checkpoint state
            state_manager = get_state_manager()
            state_manager.checkpoint()
            
            # Stop server with grace period
            await self.server.stop(grace=5)
            print("✓ Server stopped")


async def serve():
    """Main server entry point."""
    server = TaasServer()
    
    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    
    def handle_shutdown(sig):
        print(f"\nReceived signal {sig}")
        asyncio.create_task(server.stop())
    
    # Register signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: handle_shutdown(s))
    
    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()


def main():
    """Main entry point."""
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
