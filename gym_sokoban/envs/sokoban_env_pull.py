import numpy as np
from .sokoban_env import SokobanEnv, CHANGE_COORDINATES
from gym.spaces import Box
from gym.spaces.discrete import Discrete
import copy

class PushAndPullSokobanEnv(SokobanEnv):

    def __init__(self,
             dim_room=(10, 10),
             max_steps=120,
             num_boxes=3,
             num_gen_steps=None):

        super(PushAndPullSokobanEnv, self).__init__(dim_room, max_steps, num_boxes, num_gen_steps)
        screen_height, screen_width = (dim_room[0] * 16, dim_room[1] * 16)
        self.observation_space = Box(low=0, high=255, shape=(screen_height, screen_width, 3))
        self.boxes_are_on_target = [False] * num_boxes
        self.action_space = Discrete(len(ACTION_LOOKUP))
        
        # _ = self.reset()

    def step(self, action, observation_mode='rgb_array'):
        assert action in ACTION_LOOKUP
        prev_dist = self.distance()
        self.num_env_steps += 1

        self.new_box_position = None
        self.old_box_position = None

        moved_box = False
        if action == 0:
            moved_player = False

        # All push actions are in the range of [0, 3]
        if action < 5:
            moved_player, moved_box = self._push(action)

        elif action < 9:
            moved_player = self._move(action)

        else:
            moved_player, moved_box = self._pull(action)

        self._calc_reward()

        # Getting closer reward
        print(self.reward_last)
        after_dist = self.distance()
        if after_dist > -1 and prev_dist > -1:
            if after_dist < prev_dist:            
                self.reward_last += self.getting_closer_reward
            elif after_dist > prev_dist:
                self.reward_last += self.getting_farther_reward
        else:
            print("distance NONE!!!!")
        done = self._check_if_done()

        # Convert the observation to RGB frame
        observation = self.render(mode=observation_mode)

        info = {
            "action.name": ACTION_LOOKUP[action],
            "action.moved_player": moved_player,
            "action.moved_box": moved_box,
        }
        if done:
            info["maxsteps_used"] = self._check_if_maxsteps()
            info["all_boxes_on_target"] = self._check_if_all_boxes_on_target()

        return observation, self.reward_last, done, info
    
    def _calc_box_from_target(self):
        box_location = self._find_box_location()
        target_location = self._find_target_location()
        if box_location is None or target_location is None:
            return -1

        distance = abs(box_location[0] - target_location[0]) + abs(box_location[1] - target_location[1])
        return distance
    
    def _find_target_location(self):
        idx = np.argmax(self.room_state == 2)
        if self.room_state.flat[idx] == 2:
            self.current_target_pos = np.unravel_index(idx, self.room_state.shape)

        return self.current_target_pos

    def _find_box_location(self):
        idx = np.argmax(self.room_state == 4)
        if self.room_state.flat[idx] == 4:
            self.current_box_pos = np.unravel_index(idx, self.room_state.shape)

        return self.current_box_pos
    
    def _pull(self, action):
        """
        Moves the player to the next field, if it is not occupied.
        :param action:
        :return: Boolean, indicating a change of the room's state
        """
        change = CHANGE_COORDINATES[(action - 1) % 4]
        new_position = self.player_position + change
        current_position = self.player_position.copy()
        pull_content_position = self.player_position - change

        # Move player if the field in the moving direction is either
        # an empty field or an empty box target.
        if self.room_state[new_position[0], new_position[1]] in [1, 2]:
            self.player_position = new_position
            self.room_state[(new_position[0], new_position[1])] = 5
            self.room_state[current_position[0], current_position[1]] = \
                self.room_fixed[current_position[0], current_position[1]]

            box_next_to_player = self.room_state[pull_content_position[0], pull_content_position[1]] in [3, 4]
            if box_next_to_player:
                # Move Box
                box_type = 4
                if self.room_fixed[current_position[0], current_position[1]] == 2:
                    box_type = 3
                self.room_state[current_position[0], current_position[1]] = box_type
                self.room_state[pull_content_position[0], pull_content_position[1]] = \
                    self.room_fixed[pull_content_position[0], pull_content_position[1]]

            return True, box_next_to_player

        return False, False

    def get_action_lookup(self):
        return ACTION_LOOKUP

    def get_action_meanings(self):
        return ACTION_LOOKUP


ACTION_LOOKUP = {
    0: 'no operation',
    1: 'push up',
    2: 'push down',
    3: 'push left',
    4: 'push right',
    5: 'move up',
    6: 'move down',
    7: 'move left',
    8: 'move right',
    9: 'pull up',
    10: 'pull down',
    11: 'pull left',
    12: 'pull right',
}

