# mujoco_ros

Wrapper, tools for using ROS with the MuJoCo simulator.

# download mujoco binary
## https://github.com/deepmind/mujoco/releases/tag/2.2.2 
mkdir -p ~/.mujoco && cd ~/.mujoco 
wget https://github.com/deepmind/mujoco/releases/download/2.2.2/mujoco-2.2.2-linux-x86_64.tar.gz
unzip mujoco-2.2.2-linux-x86_64.tar.gz

# glfw
sudo apt-get install libglfw3
sudo apt-get install libglfw3-dev
