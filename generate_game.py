import json
import random

def get_extrinsic_words():
    json_filename = 'words_data/common_nouns_extrinsic.json'
    with open(json_filename, 'r') as json_file:
        data = json.load(json_file)
    return data
def get_codenames_words():
    json_filename = 'words_data/codenames_words.json'
    with open(json_filename, 'r') as json_file:
        data = json.load(json_file)
    return data
def get_game_board(real_codenames_words=True):
    game = dict()
    if real_codenames_words:
        game['words'] = random.sample(get_codenames_words(), 25)
        game['words'] = [x.lower() for x in game['words']]
    else:
        game['words'] = random.sample(get_extrinsic_words(), 25)
        game['words'] = [x.lower() for x in game['words']]
    #team that goes first (blue) has one extra card to guess since they go first (9 total)
    game['blue_words'] = random.sample(game['words'], 9)
    remaining = [x for x in game['words'] if x not in game['blue_words']]
    #red team goes second and has 8 total words to guess
    game['red_words'] = random.sample(remaining, 8)
    #neutral words can be guessed with no penalty
    game['neutral_words'] = [x for x in remaining if x not in game['red_words']]
    #if assassin is guessed, then the guessing team loses instantly
    game['assassin'] = random.choice(game['neutral_words'])
    game['neutral_words'].remove(game['assassin'])

    return game

if __name__ == '__main__':
    game = get_game_board(real_codenames_words=True)
    print(game)