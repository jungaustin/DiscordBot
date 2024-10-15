import requests
import json
from PIL import Image
from io import BytesIO
import asyncio
from discord import File, Embed



deck_of_cards_url = 'https://www.deckofcardsapi.com/api/deck/new/shuffle/?deck_count=1'
draw_a_card_url = 'https://www.deckofcardsapi.com/api/deck/{}/draw/?count={}'
back_of_card = 'https://www.deckofcardsapi.com/static/img/back.png'


royals = {
            'KING': 10,
            'QUEEN': 10,
            'JACK' : 10,
            'ACE' : 11
        }
    
def play_blackjack(params = {}):
    params['deck_count'] = 4
    response1 = requests.get(deck_of_cards_url, params=params)
    if response1.status_code == 200:
        data = response1.json()
    else:
        return
    player_hand = []
    computer_hand = []

    starting_cards_request = requests.get(draw_a_card_url.format(data['deck_id'], 8))
    if starting_cards_request.status_code == 200:
        starting_cards = starting_cards_request.json()
    else:
        return
    player_hand.append(starting_cards['cards'][0])
    player_hand.append(starting_cards['cards'][2])
    computer_hand.append(starting_cards['cards'][1])
    computer_hand.append(starting_cards['cards'][3])
    return player_hand, computer_hand, starting_cards['deck_id']

def hit(hand, deck_id):
    draw_card_request = requests.get(draw_a_card_url.format(deck_id, 1))
    if draw_card_request.status_code == 200:
        drawn_card = draw_card_request.json()
    hand.append(drawn_card['cards'][0])
    curr_val = count_val(hand)
    bust = curr_val > 21
    return bust

def stand(computer_hand, deck_id):
    curr_val = 0
    num_aces = 0
    curr_val = count_val(computer_hand)
    while(curr_val <= 17):
        hit(computer_hand, deck_id)
        curr_val = count_val(computer_hand)
    bust = curr_val > 21
    return bust

def count_val(hand):
    curr_val = 0
    num_aces = 0
    for card in hand:
        if card['value'] in royals:
            if card['value'] == 'ACE':
                num_aces += 1
            curr_val += royals[card['value']]
        else:
            curr_val += int(card['value'])
    while curr_val > 21 and num_aces > 0:
        curr_val-=10
        num_aces-=1
    return curr_val

async def check_response(bot, ctx, player_hand, computer_hand, deck_id):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['h', 's']
    try:
        message = await bot.wait_for('message', check=check, timeout=30)
        if check(message):
            if message.content.lower() == 'h':
                bust = hit(player_hand, deck_id)
                return player_hand, computer_hand, deck_id, bust
            else:
                bust = stand(computer_hand, deck_id)
                return player_hand, computer_hand, deck_id, True
    except asyncio.TimeoutError:
        await ctx.send("Time is up! Automatically Stood!")
        bust = stand(computer_hand, deck_id)
        return player_hand, computer_hand, deck_id, bust
    
async def send_hand(ctx, hand, name, done = False):
        image_binary = combine_images(hand, name == 'Computer', done)
        embed = Embed(title=f"{name}'s Cards")
        embed.set_image(url="attachment://blackjack_combined.png")
        await ctx.send(file=File(fp=image_binary, filename='blackjack_combined.png'), embed=embed)
        embed.set_image(url="attachment://blackjack_combined.png")

def combine_images(hand, computer = False, done = False):
    if computer and len(hand) == 2 and not done:
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