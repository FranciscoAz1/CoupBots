from proto.game_proto import game_proto, GameMessage
from proto.game_proto import ACT, OK, CHAL, BLOCK, SHOW, LOSE, COINS, DECK, CHOOSE, KEEP, HELLO, PLAYER, START, READY, TURN, EXIT, ILLEGAL
from .game.state_machine import PlayerState, Tag
from .game.core import *
from .player import InformedPlayer
import random
from loguru import logger



class CoupBot(InformedPlayer):
    """
    CoopBot player class.
    
    Attributes:
        alive (bool): Flag for whether the player is alive or not.
        checkout (SimpleQueue): Queue used to send messages to the server. The queue is thread-safe and can be used by multiple threads.
        coins (int): Number of coins the player has.
        deck (list[str]): List of cards in the player's deck.
        exchange_cards (list[str]): List of cards to exchange with the deck.
        id (str): Player ID.
        is_root (bool): Flag for whether the player is the root player or not.
        msg (GameMessage): Message to be sent to the server.
        players (dict[str, PlayerSim]): Dictionary of players in the game.
        possible_messages (list[str]): List of possible messages the player can send.
        rcv_msg (GameMessage): Last received message.
        ready (bool): Flag for whether the player is ready or not.
        replied (bool): Flag for whether the player has replied to the last message or not.
        state (PlayerState): State of the player.
        tag (Tag): Tag for the player. Used to identify the player in the game.
        term (Terminal): Terminal used to write messages manually.
        terminate_after_death (bool): Flag for whether the player should terminate after its own death.
        turn (bool): Flag for whether it is the player's turn or not.
    
    Methods:
        choose_message(): Choose a message to send to the server based on the current state of the game.
        
    """

    def __init__(self):
        super().__init__()

    def choose_message(self) -> None:
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        
        # Implement your bot here
        # Example: choose a random message from possible messages
        self.msg = GameMessage(random.choice(self.possible_messages))


class TestBot(InformedPlayer):    
    """TestBot player class."""

    def __init__(self):
        super().__init__()

    def choose_message(self):
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        self.msg = GameMessage(random.choice(self.possible_messages)) # choose random
        # self.msg = GameMessage(self.possible_messages[-1]) # choose last
        return
        
        # test with priority choices
        msgs: list[GameMessage] = []
        for m in self.possible_messages:
            msgs.append(GameMessage(m))
        for m in msgs:
            if m.command == ACT and m.action == ASSASSINATE:
                self.msg = m
                return
        for m in msgs:
            if m.command == ACT and m.action == INCOME:
                self.msg = m
                return
        for m in msgs:
            if m.command == BLOCK and len(self.deck) == 1:
                self.msg = m
                return

import ollama
class AICoupBot(InformedPlayer):
    """
    CoopBot player class.
    
    Attributes:
        alive (bool): Flag for whether the player is alive or not.
        checkout (SimpleQueue): Queue used to send messages to the server. The queue is thread-safe and can be used by multiple threads.
        coins (int): Number of coins the player has.
        deck (list[str]): List of cards in the player's deck.
        exchange_cards (list[str]): List of cards to exchange with the deck.
        id (str): Player ID.
        is_root (bool): Flag for whether the player is the root player or not.
        msg (GameMessage): Message to be sent to the server.
        players (dict[str, PlayerSim]): Dictionary of players in the game.
        possible_messages (list[str]): List of possible messages the player can send.
        rcv_msg (GameMessage): Last received message.
        ready (bool): Flag for whether the player is ready or not.
        replied (bool): Flag for whether the player has replied to the last message or not.
        state (PlayerState): State of the player.
        tag (Tag): Tag for the player. Used to identify the player in the game.
        term (Terminal): Terminal used to write messages manually.
        terminate_after_death (bool): Flag for whether the player should terminate after its own death.
        turn (bool): Flag for whether it is the player's turn or not.
    
    Methods:
        choose_message(): Choose a message to send to the server based on the current state of the game.
        
    """

    def __init__(self):
        super().__init__()

    def choose_message(self) -> None:
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        
        # Implement your bot here
        # Example: choose a random message from possible messages
        self.msg = GameMessage(random.choice(self.possible_messages))

import ollama
class AICoupBot(InformedPlayer):
    """TestBot player class."""

    def __init__(self):
        super().__init__()

    def choose_message(self):
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        # TODO: Implement a AI BOT here
        # The AI bot should get context from the game history and choose a message, from the self.possible_messages
        # Use ollama that is running on a ollama server
        ollama_client = ollama.AsyncClient(host="localhost", port=11434, timeout=10000)

        # Get messages from game history
        messages = []
        # TODO: create a system prompt signaling this is an AI bot playing the game coup
        system_prompt = """You are an AI bot playing the card game Coup. 
        
Game rules:
- Each player starts with 2 character cards and 2 coins
- The game is about deception, bluffing, and strategy
- Actions include: Income (1 coin), Foreign Aid (2 coins), Coup (7 coins, eliminate opponent's card), Tax (3 coins, requires Duke), Steal (2 coins from opponent, requires Captain), Assassinate (3 coins, eliminate opponent's card, requires Assassin), Exchange (swap cards, requires Ambassador)
- Players can block or challenge actions
- Characters: Duke (blocks Foreign Aid, takes Tax), Assassin (Assassinate), Captain (Steal, blocks Steal), Ambassador (Exchange, blocks Steal), Contessa (blocks Assassination)

Your task:
1. Analyze the game state and history
2. Choose ONE message from the possible_messages list
3. Return ONLY the exact message text from the possible_messages list
4. Consider your cards, coins, and opponent actions when deciding

DO NOT create new messages or modify the existing ones. ONLY select from the provided list."""
        messages.append({"role": "system", "content": system_prompt})
        messages.extend(self.game_history)
        # prepare a better prompt with the possible messages, explain why each of the messages would be useful in the game of coup
        messages.append({"role": "user", "content": self.possible_messages})

        # TODO: get the response from the ollama server
        response = ollama_client.chat(model="quen2.5:latest", messages=messages, stream=False)

        model_response = response["message"]["content"]

        # TODO: find possible messages in model_response, and return the first one,
        def find_message_in_response(response_text, possible_messages):
            """
            Find a valid message from the possible_messages list in the model's response text.
            Returns the first valid message found, or None if no valid message is found.
            """
            # First, try to find an exact match
            for message in possible_messages:
                if message in response_text:
                    logger.info(f"Found exact message match: {message}")
                    return message
            
            # If no exact match, look for message components (ACT, BLOCK, etc.)
            # This handles cases where the model might have formatted the message differently
            for message in possible_messages:
                message_parts = message.split()
                # Check if all parts of a message appear in the response in the correct order
                if all(part in response_text for part in message_parts):
                    logger.info(f"Found partial message match: {message}")
                    return message
            
            return None
        
        selected_message = find_message_in_response(model_response, self.possible_messages)
        
        if selected_message:
            self.msg = GameMessage(selected_message)
            logger.info(f"AI selected message: {selected_message}")
            return
                # TODO: If not rechat with the model to get a valid message, try gleaning times.
        # If no valid message was found, try one more time with a more specific prompt
        if not selected_message:
            logger.warning("No valid message found in model response. Trying again with more specific prompt.")
            def retry_llm():
                retry_prompt = f"""I need you to select ONE message from this list of possible actions. 
                
    Available messages:
    {', '.join(self.possible_messages)}

    IMPORTANT: Your response should contain ONLY ONE of these exact messages. Do not add any explanation, just return the message."""
                
                try:
                    # Retry with more specific prompt
                    retry_messages = [
                        {"role": "system", "content": "You are playing the game Coup. Select exactly one message from the provided options."},
                        {"role": "user", "content": retry_prompt}
                    ]
                    
                    retry_response = ollama_client.chat(model="quen2.5:latest", messages=retry_messages, stream=False)
                    retry_model_response = retry_response["message"]["content"]
                    
                    selected_message = find_message_in_response(retry_model_response, self.possible_messages)
                    
                    if selected_message:
                        self.msg = GameMessage(selected_message)
                        logger.info(f"AI selected message after retry: {selected_message}")
                        return
                    else:
                        logger.warning("No valid message found after retry. Using fallback strategy.")
                except Exception as e:
                    logger.error(f"Error during retry: {str(e)}")
            retry_llm()
        # Fallback to a strategic selection if AI failed to provide a valid message
        msgs = [GameMessage(m) for m in self.possible_messages]
        
        # Strategic priority-based fallback
        def priority_based_fallback():
            # 1. If we have enough coins, coup is usually the best move
            for m in msgs:
                if m.command == ACT and m.action == COUP and self.coins >= 7:
                    self.msg = m
                    logger.info("Fallback: Using COUP action")
                    return
                    
            # 2. Assassinate is powerful if we have the card
            for m in msgs:
                if m.command == ACT and m.action == ASSASSINATE and "ASSASSIN" in self.deck:
                    self.msg = m
                    logger.info("Fallback: Using ASSASSINATE action")
                    return
                    
            # 3. Block assassination if we have contessa
            for m in msgs:
                if m.command == BLOCK and "CONTESSA" in self.deck:
                    self.msg = m
                    logger.info("Fallback: Blocking with CONTESSA")
                    return
            
            # 4. Tax is good for getting coins if we have duke
            for m in msgs:
                if m.command == ACT and m.action == TAX and "DUKE" in self.deck:
                    self.msg = m
                    logger.info("Fallback: Using TAX action")
                    return
                    
            # 5. Income is a safe choice
            for m in msgs:
                if m.command == ACT and m.action == INCOME:
                    self.msg = m
                    logger.info("Fallback: Using INCOME action")
                    return
        
        priority_based_fallback()
        # Last resort: random choice
        self.msg = GameMessage(random.choice(self.possible_messages))
        logger.info(f"Fallback: Using random message: {self.msg}")
        return

