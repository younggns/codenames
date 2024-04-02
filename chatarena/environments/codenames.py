from typing import List, Union

from ..agent import SIGNAL_END_OF_CONVERSATION, Moderator
from ..config import AgentConfig, EnvironmentConfig
from ..message import Message, MessagePool
from .base import Environment, TimeStep, register_env

import re


@register_env
class Codenames(Environment):
    """
    Turn-based fully observable conversation environment.

    Next speaker order is either parallel or round-robin.
    """

    type_name = "codenames"

    def __init__(self, player_names: List[str], all_words, valid_words, one_word: bool = True, parallel: bool = False, **kwargs):
        super().__init__(player_names=player_names, parallel=parallel, **kwargs)

        self.parallel = parallel

        # The "state" of the environment is maintained by the message pool
        self.message_pool = MessagePool()

        self._current_turn = 0
        self._next_player_idx = 0
        
        # words in the game
        self.valid_words = valid_words
        self.all_words = all_words
        
        # guesser could only guess one word in each turn
        self.one_word = one_word

    def reset(self):
        self._current_turn = 0
        self._next_player_idx = 0
        self.message_pool.reset()
        
        self.correct_words = []
        self.incorrect_words = []     
        self.repeated_words = []
        
        text = f"The grid of words are {self.all_words}."
        self._moderator_speak(text, visible_to='all')
        
        text = f"All the words in your team are {self.valid_words}. Now please give a one word hint followed by a number indicating how many words on the grid relate to the hint. The format of the output should be [hint, number]"
        self._moderator_speak(text, visible_to='Spymaster')
        
        init_timestep = TimeStep(
            observation=[], reward=self.get_zero_rewards(), terminal=False
        )
        return init_timestep

    def to_config(self) -> EnvironmentConfig:
        return EnvironmentConfig(
            env_type=self.type_name,
            player_names=self.player_names,
            parallel=self.parallel,
        )

    def print(self):
        self.message_pool.print()

    def get_next_player(self) -> str:
        """Get the next player."""
        return self.player_names[self._next_player_idx]

    def get_observation(self, player_name=None) -> List[Message]:
        """Get observation for the player."""
        if player_name is None:
            return self.message_pool.get_all_messages()
        else:
            return self.message_pool.get_visible_messages(
                player_name, turn=self._current_turn
            )

    def is_terminal(self) -> bool:
        """Check if the conversation is over."""
        # If the last message is the signal, then the conversation is over
        if self.message_pool.last_message.content.startswith(
            SIGNAL_END_OF_CONVERSATION
        ):
            return True
        
    def guesser_turn(self, message):
        if self.one_word:
            guess_word, check = self.guess_judge_one_word(message.content)
            if check:
                # guess correctly
                text = f"The word '{guess_word}' is correct, the guesser can make another guess, the guesser can only guess one word each time. The format of the output should be [word]" 
                # self.guess_list.update() # maintian all the correct words
                self._moderator_speak(text, visible_to="all")
            else:
                # guess wrong
                self._next_player_idx = (self._next_player_idx + 1) % self.num_players # switch to spymaster
                if guess_word:
                    text = f"The word '{guess_word}' is not correct. Now the spymaster give another hint."
                else:
                    text = f"Invalid guess. Now the spymaster give another hint."
                self._moderator_speak(text, visible_to="all")
                
                # Update the counters
                self._current_turn += 1
                
                text = f"The grid of words are {self.all_words}."
                self._moderator_speak(text, visible_to='all')
                
                text = f"The remaining words in your team are {self.valid_words}. Now please give a one word hint followed by a number indicating how many words on the grid relate to the hint. The format of the output should be [hint, number]"
                self._moderator_speak(text, visible_to='Spymaster')
        else:
            current_correct_words, current_incorrect_words, current_repeated_correct_words, current_repeated_incorrect_words = self.guess_judge_multi_words(message.content)
            
            text = f"\nCorrect words: {current_correct_words}, Incorrect words: {current_incorrect_words}.\nRepeated correct words: {current_repeated_correct_words}, Repeated incorrect words: {current_repeated_incorrect_words}.\nCorrect points: {len(self.correct_words)}, Incorrect points: {len(self.incorrect_words)}"
            self._moderator_speak(text, visible_to="all")
            
            self._next_player_idx = (self._next_player_idx + 1) % self.num_players # switch to spymaster
            
            # Update the counters
            self._current_turn += 1
            
            text = f"The grid of words are {self.all_words}."
            self._moderator_speak(text, visible_to='all')
            
            text = f"The remaining words in your team are {self.valid_words}. Now please give a one word hint followed by a number indicating how many words on the grid relate to the hint. The format of the output should be [hint, number]"
            self._moderator_speak(text, visible_to='Spymaster')
            

    def step(self, player_name: str, action: str) -> TimeStep:
        """
        Step function that is called by the arena.

        Args:
            player_name: the name of the player that takes the action
            action: the action that the agents wants to take
        """
        message = Message(
            agent_name=player_name, content=action, turn=self._current_turn
        )
        self.message_pool.append_message(message)
        
        # if the current player is spymaster
        if player_name == "Spymaster":
            self._next_player_idx = 1
            if self.one_word:
                text = f"Now the guesser make a guess based on the hint, the guesser can only guess one word each time. The format of the output should be [word]."
            else:
                text = f"Now the guesser make a guess based on the hint."
            self._moderator_speak(text, visible_to='Guesser')
        
        # if the current player is gusser
        # make sure if the guess is correct
        # append the result to the message
        # append which words are guessed correct and which are left?
        elif player_name == "Guesser":
            self.guesser_turn(message)
        
        # make sure if the game end: win & loss
        # if not: continue; else: end the game"
        if len(self.valid_words) == 0:
            self._moderator_speak(SIGNAL_END_OF_CONVERSATION, visible_to='all')

        timestep = TimeStep(
            observation=self.get_observation(),
            reward=self.get_zero_rewards(),
            terminal=self.is_terminal(),
        )  # Return all the messages
        return timestep
    
    def guess_judge_one_word(self, message):
        """
        Judge the answer of the guesser. \
        The guesser can only guess one word in each turn.
        """
        for i in self.all_words:
            if ' '+i+' ' in message:
                if i in self.valid_words:
                    # remove all the correct words from current valid words
                    self.valid_words.remove(i)
                    return i, True
                else: 
                    return i, False
        return None, False
    
    def guess_judge_multi_words(self, message):
        """
        Judge the answer of the guesser. \
        The guesser can guess multi words in each turn.
        """
        current_correct_words = []
        current_incorrect_words = []     
        current_repeated_correct_words = []
        current_repeated_incorrect_words = []
        
        for i in self.all_words:
            if i in message:
                if i in self.valid_words:
                    # remove all the correct words from current valid words
                    self.valid_words.remove(i)
                    self.correct_words.append(i)
                    current_correct_words.append(i)
                elif i in self.correct_words:
                    current_repeated_correct_words.append(i)
                elif i in self.incorrect_words: 
                    current_repeated_incorrect_words.append(i)
                else:
                    self.incorrect_words.append(i)
                    current_incorrect_words.append(i)
        return current_correct_words, current_incorrect_words, current_repeated_correct_words, current_repeated_incorrect_words
                    
        
    
    def _moderator_speak(self, text: str, visible_to: Union[str, List[str]] = "all"):
        """Moderator say something."""
        message = Message(
            agent_name="Moderator",
            content=text,
            turn=self._current_turn,
            visible_to=visible_to,
        )
        self.message_pool.append_message(message)