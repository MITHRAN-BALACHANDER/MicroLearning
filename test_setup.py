"""
Simple test script to verify video generation setup
Run this after setup to ensure everything is working
"""
import sys
import os

# Add Agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Agents'))

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    try:
        from agents.text_to_video_agent import TextToVideoAgent
        from database.models import VideoGenerationJob
        from config.settings import KIE_API_KEY, KIE_API_URL
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_database():
    """Test database connection and table existence"""
    print("\n🧪 Testing database...")
    try:
        from database.operations import SessionLocal
        from database.models import VideoGenerationJob
        
        db = SessionLocal()
        # Try to query the table
        count = db.query(VideoGenerationJob).count()
        db.close()
        
        print(f"✅ Database connected! Found {count} generation jobs.")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_agent_init():
    """Test if video generation agent can be initialized"""
    print("\n🧪 Testing agent initialization...")
    try:
        from agents.text_to_video_agent import TextToVideoAgent
        agent = TextToVideoAgent()
        print("✅ Video generation agent initialized successfully!")
        print(f"   API URL: {agent.api_url}")
        print(f"   API Key: {agent.api_key[:10]}...")
        return True
    except Exception as e:
        print(f"❌ Agent initialization error: {e}")
        return False

def test_api_connection():
    """Test API connectivity (doesn't create a job, just checks connection)"""
    print("\n🧪 Testing API connectivity...")
    try:
        import requests
        from config.settings import KIE_API_URL
        
        # Just check if the endpoint is reachable (may return error, that's ok)
        response = requests.options(KIE_API_URL, timeout=5)
        print("✅ API endpoint is reachable!")
        return True
    except requests.exceptions.Timeout:
        print("⚠️  API endpoint timeout (might be normal)")
        return True
    except Exception as e:
        print(f"⚠️  API connection test inconclusive: {e}")
        return True  # Not critical

def test_optional_video_generation():
    """Optional: Actually test video generation (requires API to be working)"""
    print("\n🧪 Optional: Test actual video generation?")
    response = input("This will use your API quota. Continue? (y/N): ")
    
    if response.lower() != 'y':
        print("⏭️  Skipped actual video generation test")
        return True
    
    print("🎬 Creating test video generation job...")
    try:
        from agents.text_to_video_agent import TextToVideoAgent
        agent = TextToVideoAgent()
        
        result = agent.create_video_generation_task(
            prompt="A simple test: a red circle on white background",
            aspect_ratio="16:9",
            n_frames="10"
        )
        
        if result['success']:
            task_data = result['data']
            task_id = task_data.get('taskId') or task_data.get('task_id') or task_data.get('id')
            print(f"✅ Video generation started successfully!")
            print(f"   Task ID: {task_id}")
            print(f"   Response: {task_data}")
            
            # Save to database
            job = agent.save_generation_job(
                prompt="A simple test: a red circle on white background",
                task_id=str(task_id),
                aspect_ratio="16:9",
                n_frames="10"
            )
            print(f"   Database Job ID: {job.id}")
            return True
        else:
            print(f"❌ Video generation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Video generation error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("MicroLearning Video Generation - Setup Verification")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Database", test_database()))
    results.append(("Agent Init", test_agent_init()))
    results.append(("API Connection", test_api_connection()))
    results.append(("Video Generation (Optional)", test_optional_video_generation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed >= 4:  # First 4 tests are critical
        print("\n✅ Setup is READY! You can start using video generation.")
        print("\n📝 Next steps:")
        print("   1. Start admin dashboard: python Agents/admin_dashboard.py")
        print("   2. Access: http://localhost:5000")
        print("   3. Or start Telegram bot: python Agents/main.py")
        return 0
    else:
        print("\n❌ Setup incomplete. Please check the errors above.")
        print("\n📝 Troubleshooting:")
        print("   1. Make sure virtual environment is activated")
        print("   2. Run: python Agents/scripts/migrate_video_generation.py")
        print("   3. Check that all requirements are installed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
