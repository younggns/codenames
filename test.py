import os
os.environ['OPENAI_API_KEY'] = 'OPENAI_API_KEY'

from chatarena.arena import Arena
from chatarena.agent import Player
from chatarena.backends import OpenAIChat
from chatarena.environments import Codenames
from chatarena.message import Message

from generate_game import get_game_board


# valid words and all_words taken from dataset
# valid_words = ["Pizza", "Farm", "Light", "Butterfly", "Center", "Tea", "Beijing", "Golf"]
# all_words = ["Jockey", "Disk", "Pizza", "Powder", "Fiddle",
#             "Battleship", "Farm", "Sahara", "Brush", "Light",
#             "Butterfly", "Center", "Tea", "Dwarf", "Rat",
#             "Beijing", "Wheel", "Golf", "Black Hole", "Shoot",
#             "Street", "Potato", "Wonderland", "Drawing", "Shark"]

game = get_game_board(real_codenames_words=True)
valid_words = game['blue_words']
all_words = game['words']

# will be updated
global_prompt = "You are playing a specific version of the game - Codenames. Here are the game rules:\n\n## Information and roles\nThere are two players, and two roles in the game, spymaster and guesser.\nA list of words will be first revealed to all the players.\nThen the list of valid words will be revealed to only the spymaster.\nThe guesser does not know any words in the list of valid words.\n\n## Objectives\nYour objective in the game depends on you role:\n- If you are a spymaster, your goal is to get the guesser to link as many valid words as possible into one clue word. The clue word will be associated with a number that indicates the number of words to be guessed from the list. The clue should be such that the guesser is drawn towards guessing the words from the list of valid words, and not any other word in the list of crosswords.\n- If you are a guesser, your aim is to utilize the clue word to guess the words from the list of words that aligns well with the given clue. The guesser can guess as many words as the number associated with the clue word.\n\n## Stages\nThere are two stages in the game:\n1. The giving clues stage: The spymaster gives a clue word and a number to the guesser.\n2. The guessing stage: The guesser guesses the words that align well with the given clue. The upper limit on the number of guessed words is the number given by the spymaster."
spymaster_prompt = "You are the spymaster. You need to give a one word hint to the guesser followed by a number indicating how many words on the grid relate to the hint, your hint should be inspirative and should not be the word in the 25 words."
guesser_prompt = "You are the guesser. You need to select which words you think are related to the clue. The output of your answer should only contain the words you guess."

# for multiple teams and more agents, loop and create more objects
spymaster_object = Player(name='Spymaster',
                          role_desc = spymaster_prompt,
                          global_prompt= global_prompt,
                          backend=OpenAIChat(model='gpt-3.5-turbo'))

guesser_object = Player(name='Guesser',
                          role_desc = guesser_prompt,
                          global_prompt= global_prompt,
                          backend=OpenAIChat(model='gpt-3.5-turbo'))

environ_obj = Codenames(['Spymaster', 'Guesser'], all_words, valid_words, one_word=False)

arena = Arena([spymaster_object, guesser_object], environment=environ_obj, global_prompt=global_prompt)
# arena = Arena.from_config("examples/codenames.json")
# Run the game for 10 steps
# arena.run(num_steps=50)
arena.launch_cli()

# Alternatively, you can run your own main loop
# for _ in range(10):
#     arena.step()
    # Your code goes here ...