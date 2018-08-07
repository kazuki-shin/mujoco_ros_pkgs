#!/usr/bin/env python
#
# Copyright (C) 2018 Shadow Robot Company Ltd - All Rights Reserved.
# Proprietary and Confidential. Unauthorized copying of the content in this file, via any medium is strictly prohibited.

import rospy
import rospkg
import re
from geometry_msgs.msg import Pose
from moveit_msgs.msg import CollisionObject
from mujoco_ros_msgs.msg import FreeObjectsStates
from shape_msgs.msg import SolidPrimitive
from mujoco2rviz.utilities import compare_poses, stl_to_mesh, get_object_mesh_path, get_object_name_from_instance


class Mujoco2Rviz():
    def __init__(self):
        self._model_cache = {}
        self._ignored_models = []
        self._description_repo_path = rospy.get_param('~description_repo_path',
                                                     rospkg.RosPack().get_path('sr_description_common'))
        self._static_only = rospy.get_param('~static_only', True)
        self._objects_states_subscriber = rospy.Subscriber('mujoco/model_states', FreeObjectsStates,
                                                          self.objects_states_cb)
        self._collision_object_publisher = rospy.Publisher('/collision_object', CollisionObject, queue_size=5,
                                                          latch=True)
        self._publish_objects_to_rviz()

    def objects_states_cb(self, objects_states_msg):
        for model_idx, model_instance_name in enumerate(objects_states_msg.name):
            if self._static_only and not objects_states_msg.is_static[model_idx]:
                continue

            if model_instance_name not in self._model_cache:
                try:
                    self._model_cache[model_instance_name] = self._create_collision_object_from_msg(objects_states_msg,
                                                                                                  model_idx)
                    if model_instance_name in self._ignored_models:
                        self._ignored_models.remove(model_instance_name)
                    rospy.loginfo("Added object {} to rviz".format(model_instance_name))
                except (TypeError, IOError) as e:
                    if model_instance_name not in self._ignored_models:
                        self._ignored_models.append(model_instance_name)
                        rospy.logwarn("Failed to add {} collision object: {}".format(model_instance_name, e))

            else:
                if 'mesh' == objects_states_msg.type[model_idx]:
                    if not compare_poses(objects_states_msg.pose[model_idx],
                                        self._model_cache[model_instance_name].mesh_poses[0]):
                        self._model_cache[model_instance_name].operation = CollisionObject.MOVE
                        self._model_cache[model_instance_name].mesh_poses[0] = objects_states_msg.pose[model_idx]
                else:
                    if not compare_poses(objects_states_msg.pose[model_idx],
                                        self._model_cache[model_instance_name].primitive_poses[0]):
                        self._model_cache[model_instance_name].operation = CollisionObject.MOVE
                        self._model_cache[model_instance_name].primitive_poses[0] = objects_states_msg.pose[model_idx]


    def _publish_objects_to_rviz(self):
        while not rospy.is_shutdown():
            for model_instance_name in self._model_cache.keys():
                self._collision_object_publisher.publish(self._model_cache[model_instance_name])

    def _create_collision_object_from_msg(self, message, model_idx):
        if 'mesh' == message.type[model_idx]:
            collision_object = self._create_collision_object_from_mesh(message.name[model_idx],
                                                                      message.pose[model_idx])
        else:
            collision_object = self._create_collision_object_from_primitive(message.name[model_idx],
                                                                           message.pose[model_idx],
                                                                           message.type[model_idx],
                                                                           message.size[model_idx].data)
        return collision_object

    def _create_collision_object_from_mesh(self, model_instance_name, model_pose):
        collision_object = self._create_collision_object_base(model_instance_name)
        object_type = get_object_name_from_instance(model_instance_name)
        object_mesh_path = get_object_mesh_path(object_type, self._description_repo_path)
        object_mesh = stl_to_mesh(object_mesh_path)
        collision_object.meshes = [object_mesh]
        collision_object.mesh_poses = [model_pose]
        return collision_object

    def _create_collision_object_from_primitive(self, model_instance_name, model_pose, model_type, size):
        collision_object = self._create_collision_object_base(model_instance_name)
        primitive = SolidPrimitive()
        if 'box' == model_type:
            primitive.type = SolidPrimitive.BOX
            primitive.dimensions = [i * 2 for i in size]
        elif 'cylinder' == model_type:
            primitive.type = SolidPrimitive.CYLINDER
            primitive.dimensions = [size[1] * 2, size[0]]
        elif 'sphere' == model_type:
            primitive.type = SolidPrimitive.SPHERE
            primitive.dimensions = [size[0]]
        else:
            raise TypeError("Primitive type {} not supported".format(model_type))
        collision_object.primitives.append(primitive)
        collision_object.primitive_poses.append(model_pose)
        return collision_object

    def _create_collision_object_base(self, model_instance_name):
        collision_object = CollisionObject()
        collision_object.header.frame_id = 'world'
        collision_object.id = '{}__link'.format(model_instance_name)
        collision_object.operation = CollisionObject.ADD
        return collision_object


if __name__ == '__main__':
    rospy.init_node('mujoco_to_rviz', anonymous=True)
    m2m = Mujoco2Rviz()
