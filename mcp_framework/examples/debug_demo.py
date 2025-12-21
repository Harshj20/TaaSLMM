"""Example: Debug Context Manager demonstration."""

import asyncio
from mcp_framework.server.debug_manager import get_debug_manager
from mcp_framework.storage.database import init_database


async def demo_debug_learning():
    """Demonstrate error learning and resolution suggestions."""
    print("="*60)
    print("Demo: Debug Context Manager")
    print("="*60)
    
    # Initialize
    init_database("sqlite:///debug_demo.db")
    debug_mgr = get_debug_manager()
    
    # Simulate error 1: Missing parameter
    print("\n1. Capturing Error: Missing Parameter")
    print("-"*60)
    
    try:
        raise ValueError("Missing required parameter 'model_name'")
    except ValueError as e:
        error_id = await debug_mgr.capture_error(
            error=e,
            tool_name="finetune",
            inputs={"dataset_id": "123"},
            stack_trace="..."
        )
        print(f"✓ Captured error: {error_id[:8]}")
    
    # Add resolution
    print("\n2. Adding Resolution")
    print("-"*60)
    
    resolution_id = await debug_mgr.add_resolution(
        error_signature_id=error_id,
        resolution_type="parameter_change",
        resolution_data={
            "parameter": "model_name",
            "new_value": "meta-llama/Llama-2-7b"
        }
    )
    print(f"✓ Added resolution: {resolution_id[:8]}")
    
    # Mark as successful
    await debug_mgr.mark_resolution_success(resolution_id, success=True)
    await debug_mgr.mark_resolution_success(resolution_id, success=True)
    await debug_mgr.mark_resolution_success(resolution_id, success=False)
    print(f"✓ Updated success rate: 66.7%")
    
    # Simulate same error again
    print("\n3. Getting Debug Hints for Same Error")
    print("-"*60)
    
    try:
        raise ValueError("Missing required parameter 'model_name'")
    except ValueError as e:
        hints = await debug_mgr.get_debug_hints(
            error=e,
            tool_name="finetune",
            min_confidence=0.5
        )
        
        if hints:
            print(f"✓ Retrieved {len(hints)} debug hint(s):")
            for i, hint in enumerate(hints, 1):
                print(f"\n  Hint {i}:")
                print(f"    Suggestion: {hint.suggestion}")
                print(f"    Confidence: {hint.confidence:.1%}")
                print(f"    Historical Success: {hint.historical_success_rate:.1%}")
        else:
            print("  No hints available")
    
    # System stats
    print("\n4. Debug System Statistics")
    print("-"*60)
    
    stats = await debug_mgr.get_system_stats()
    print(f"  Total Unique Errors: {stats['total_unique_errors']}")
    print(f"  Total Resolutions: {stats['total_resolutions']}")
    print(f"  Error Types: {stats['error_types']}")
    
    print("\n" + "="*60)
    print("✓ Debug Context Demo Complete!")
    print("="*60)
    print("\nKey Features Demonstrated:")
    print("  - Error signature hashing")
    print("  - Resolution tracking")
    print("  - Success rate calculation")
    print("  - Intelligent hint generation")


if __name__ == "__main__":
    asyncio.run(demo_debug_learning())
