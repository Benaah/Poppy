# Poppy Robot - Development Documentation

Welcome to the Poppy Robot development documentation. This directory contains comprehensive guides for developing, testing, and deploying the Poppy system.

## Documentation Structure

- `architecture/` - System architecture and design decisions
- `api/` - API documentation for SDK and ROS2 interfaces  
- `hardware/` - Hardware assembly guides and schematics
- `firmware/` - ESP32 firmware development guides
- `ros2/` - ROS2 package documentation
- `tutorials/` - Step-by-step development tutorials
- `deployment/` - Production deployment guides

## Quick Links

- [Getting Started](./tutorials/01_getting_started.md)
- [ROS2 Package Overview](./ros2/package_overview.md)
- [Hardware Assembly Guide](./hardware/assembly_guide.md)
- [API Reference](./api/sdk_reference.md)
- [Contributing Guidelines](../CONTRIBUTING.md)

## Development Workflow

1. **Setup Development Environment**
   ```bash
   ./tools/scripts/init_workspace.sh
   source ros2_ws/install/setup.bash
   ```

2. **Create a New Feature**
   ```bash
   git checkout -b feature/your-feature-name
   # Make changes
   colcon build --packages-select poppy_<package>
   ```

3. **Test Your Changes**
   ```bash
   colcon test --packages-select poppy_<package>
   ros2 launch poppy_bringup test.launch.py
   ```

4. **Submit for Review**
   ```bash
   git commit -m "feat: description of your feature"
   git push origin feature/your-feature-name
   # Create Pull Request
   ```

## Resources

- [ROS2 Humble Documentation](https://docs.ros.org/en/humble/)
- [Jetson Nano Developer Guide](https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit)
- [Picovoice Porcupine Docs](https://picovoice.ai/docs/porcupine/)
- [Google Assistant SDK](https://developers.google.com/assistant/sdk)

---

For questions or issues, please open a GitHub Issue or contact the development team.
