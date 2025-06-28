✅ Enhanced WhisperS2T Appliance v0.5.0 ready!")
        logger.info("🎉 All systems operational - accepting connections")
        
        # Start server
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("🛑 Keyboard interrupt received")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)
    finally:
        logger.info("🔄 Server shutdown completed")

if __name__ == "__main__":
    # Check if running as root (for systemd service)
    if os.geteuid() == 0:
        print("⚠️  Warning: Running as root - switching to whisper user recommended")
    
    # Start the appliance
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Appliance stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
