/*
* Copyright 2018 Shadow Robot Company Ltd.
*
* This program is free software: you can redistribute it and/or modify it
* under the terms of the GNU General Public License as published by the Free
* Software Foundation version 2 of the License.
*
* This program is distributed in the hope that it will be useful, but WITHOUT
* ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
* FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
* more details.
*
* You should have received a copy of the GNU General Public License along
* with this program. If not, see <http://www.gnu.org/licenses/>.
*
* @file   mujoco_ros_control.h
* @author Giuseppe Barbieri <giuseppe@shadowrobot.com>
* @brief  Node to allow ros_control hardware interfaces to be plugged into mujoco
**/

#ifndef MUJOCO_ROS_CONTROL_MUJOCO_ROS_CONTROL_H
#define MUJOCO_ROS_CONTROL_MUJOCO_ROS_CONTROL_H

// Boost
#include <boost/shared_ptr.hpp>
#include <boost/thread.hpp>

// ROS
#include <ros/ros.h>
#include <pluginlib/class_loader.h>
#include <std_msgs/Bool.h>
#include <ros/package.h>

// Mujoco dependencies
#include <mujoco/mujoco.h>
#include <mujoco/mjdata.h>
#include <mujoco/mjmodel.h>

#include <fstream>
#include <string>
#include <iostream>
#include <vector>
#include <map>

// ros_control
#include <mujoco_ros_control/robot_hw_sim.h>
#include <mujoco_ros_control/robot_hw_sim_plugin.h>

// msgs
#include "geometry_msgs/Pose.h"
#include "std_msgs/Float64MultiArray.h"
#include "mujoco_ros_msgs/ModelStates.h"

#include <controller_manager/controller_manager.h>
#include <transmission_interface/transmission_parser.h>

// openGL stuff
#include <GLFW/glfw3.h>
#include <mujoco_ros_control/visualization_utils.h>

#include <rosgraph_msgs/Clock.h>

namespace mujoco_ros_control
{

class MujocoRosControl
{
public:
  MujocoRosControl();
  virtual ~MujocoRosControl();

  // initialize params and controller manager
  bool init(ros::NodeHandle &nodehandle);

  // step update function
  void update();

  // pointer to the mujoco model
  mjModel* mujoco_model;
  mjData* mujoco_data;

  // number of degrees of freedom
  unsigned int n_dof_;

  // number of free joints in simulation
  unsigned int n_free_joints_;

protected:
  // free or static object
  enum Object_State { STATIC = true, FREE = false };

  // get the URDF XML from the parameter server
  std::string get_urdf(std::string param_name) const;

  // setup initial sim environment
  void setup_sim_environment();

  // parse transmissions from URDF
  bool parse_transmissions(const std::string& urdf_string);

  // get number of degrees of freedom
  void get_number_of_dofs();

  // publish simulation time to ros clock
  void publish_sim_time();

  // check for free joints in the mujoco model
  void check_objects_in_scene();

  // publish free objects
  void publish_objects_in_scene();

  // transform type id to type name
  std::string geom_type_to_string(int geom_id);

  // node handles
  ros::NodeHandle robot_node_handle;

  // interface loader
  boost::shared_ptr<pluginlib::ClassLoader<mujoco_ros_control::RobotHWSimPlugin> > robot_hw_sim_loader_;

  // strings
  std::string robot_namespace_;
  std::string robot_description_param_;
  std::string robot_model_path_;
  std::string key_path_ = "/home/user/mjpro150/bin/mjkey.txt";

  // vectors
  std::vector<int> mujoco_ids;
  std::vector<int>::iterator it;
  std::vector<std::string> robot_link_names_;
  std::map<int, Object_State> objects_in_scene_;

  // transmissions in this plugin's scope
  std::vector<transmission_interface::TransmissionInfo> transmissions_;

  // robot simulator interface
  boost::shared_ptr<mujoco_ros_control::RobotHWSimPlugin> robot_hw_sim_;

  // controller manager
  boost::shared_ptr<controller_manager::ControllerManager> controller_manager_;

  // simulated clock
  ros::Publisher pub_clock_;
  int pub_clock_frequency_;
  ros::Time last_pub_clock_time_;

  // timing
  ros::Duration control_period_;
  ros::Time last_update_sim_time_ros_;
  ros::Time last_write_sim_time_ros_;

  // publishing
  ros::Publisher objects_in_scene_publisher = robot_node_handle.advertise<mujoco_ros_msgs::ModelStates>
                                                                         ("/mujoco/model_states", 1000);
};
}  // namespace mujoco_ros_control
#endif  // MUJOCO_ROS_CONTROL_MUJOCO_ROS_CONTROL_H
