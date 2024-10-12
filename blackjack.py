import requests
import json
from PIL import Image
from io import BytesIO



deck_of_cards_url = 'https://www.deckofcardsapi.com/api/deck/new/shuffle/?deck_count=1'
draw_a_card_url = 'https://www.deckofcardsapi.com/api/deck/<<deck_id>>/draw/?count=2'
back_of_card = 'https://www.deckofcardsapi.com/static/img/back.png'

def play_blackjack(params = {}):
    params['deck_count'] = 1
    response1 = requests.get(deck_of_cards_url, params=params)
    if response1.status_code is 200:
        data = response1.json()
    else:
        return
    player_hand = []
    computer_hand = []

    starting_cards_request = requests.get('https://www.deckofcardsapi.com/api/deck/'+ data['deck_id'] + '/draw/?count=4')
    if starting_cards_request.status_code is 200:
        starting_cards = starting_cards_request.json()
    else:
        return
    player_hand.append(starting_cards['cards'][0])
    player_hand.append(starting_cards['cards'][2])
    computer_hand.append(starting_cards['cards'][1])
    computer_hand.append(starting_cards['cards'][3])
    return player_hand, computer_hand

def combine_images(hand, computer = False):
    if computer and len(hand) is 2:
        images = []
        response = requests.get(hand[0]['image'])
        images.append(Image.open(BytesIO(response.content)))
        response = requests.get(back_of_card)
        images.append(Image.open(BytesIO(response.content)))
        widths, heights = zip(*(i.size for i in images))
        total_width = sum(widths)
        max_height = max(heights)
        combined_image = Image.new('RGB', (total_width, max_height))
        x_offset = 0
        for img in images:
            combined_image.paste(img, (x_offset, 0))
            x_offset += img.size[0]
        image_binary = BytesIO()
        combined_image.save(image_binary, format='PNG')
        image_binary.seek(0)
        return image_binary
    else:
        images = []
        for card in hand:
            response = requests.get(card['image'])
            img = Image.open(BytesIO(response.content))
            images.append(img)
        widths, heights = zip(*(i.size for i in images))
        total_width = sum(widths)
        max_height = max(heights)
        combined_image = Image.new('RGB', (total_width, max_height))
        x_offset = 0
        for img in images:
            combined_image.paste(img, (x_offset, 0))
            x_offset += img.size[0]
        image_binary = BytesIO()
        combined_image.save(image_binary, format='PNG')
        image_binary.seek(0)
        return image_binary