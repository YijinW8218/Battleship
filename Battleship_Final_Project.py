###Imports
import pygame
from pygame.locals import *
import sys
from sys import exit
import random
import os
from pathlib import Path


# Resolve all relative asset paths from this project's directory, even when the
# game is started from a different working directory.
PROJECT_DIR = Path(__file__).resolve().parent
os.chdir(PROJECT_DIR)


# AI state to track current mode and targets
enemy_ai_state = {
    "mode": "hunt",
    "target_queue": [],
    "first_hit_pos": None,
    "target_direction": None
}


# Stores x,y corrdinates for enemy ai
enemy_hunt_targets = []

# Handles creating, randomly placing, and drawing the enemy ships during gameplay
class EnemyShipSprite(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((1000, 800), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(0,0))


        # Define ship lengths 
        self.ship_lengths = [200, 160, 120, 120, 80]  # carrier(5), battleship(4), destroyer(3), submarine(3), patrol(2)


        self.enemy_ships = []  # list of dicts: { "rect": ..., "name": ..., "health": ... }

        # Load enemy ship images
        self.ship_images = [
            pygame.image.load("assets/carrier.png").convert_alpha(),
            pygame.image.load("assets/battleship.png").convert_alpha(),
            pygame.image.load("assets/destroyer.png").convert_alpha(),
            pygame.image.load("assets/submarine.png").convert_alpha(),
            pygame.image.load("assets/patrolboat.png").convert_alpha()
        ]

        # Rotate images to be horizontal
        self.ship_images[0] = pygame.transform.rotate(self.ship_images[0], -90)
        self.ship_images[1] = pygame.transform.rotate(self.ship_images[1], -90)
        self.ship_images[2] = pygame.transform.rotate(self.ship_images[2], -90)
        self.ship_images[3] = pygame.transform.rotate(self.ship_images[3], -90)
        self.ship_images[4] = pygame.transform.rotate(self.ship_images[4], -90)

        # Then resize them properly
        self.ship_images[0] = pygame.transform.scale(self.ship_images[0], (200, 40))  # Carrier
        self.ship_images[1] = pygame.transform.scale(self.ship_images[1], (160, 40))  # Battleship
        self.ship_images[2] = pygame.transform.scale(self.ship_images[2], (120, 40))  # Destroyer
        self.ship_images[3] = pygame.transform.scale(self.ship_images[3], (120, 40))  # Submarine
        self.ship_images[4] = pygame.transform.scale(self.ship_images[4], (80, 40))   # Patrol boat

        # Place all ships randomly within placing algorithim 
        self.place_ships_randomly()

    # Determines where the ships will be placed within the bounds
    def place_ships_randomly(self):

        # Ship sizes
        ship_info = [
            ("Carrier", 5, 200),
            ("Battleship", 4, 160),
            ("Destroyer", 3, 120),
            ("Submarine", 3, 120),
            ("Patrol Boat", 2, 80)
        ]

        # Separates ships into types for organization when placing
        big_ships = []
        small_ships = []
        ships_to_place = ship_info.copy()

        # Chance for ships to spawn together
        cluster_mode = False
        if random.random() < 0.1:  # 10% chance to cluster two small ships
            cluster_mode = True

        # Gets a ship from list and place them accordingly
        while ships_to_place:
            name, size, length = ships_to_place.pop(0)
            placed = False

            # Determine horizontal or Vertical Placement
            while not placed:
                orientation = random.choice(['horizontal', 'vertical'])

                # Favor horizontal for big ships
                if name in ["Carrier", "Battleship"] and random.random() < 0.7:
                    orientation = 'horizontal'

                # Edge bias
                if random.random() < 0.4:
                    if orientation == 'horizontal':
                        x = random.choice([650, 1010 - length])
                        y = random.randrange(200, 600, 40)
                    else:
                        x = random.randrange(650, 1050, 40)
                        y = random.choice([200, 560 - length])
                else:
                    if orientation == 'horizontal':
                        x = random.randrange(650, 1050 - length, 40)
                        y = random.randrange(200, 600, 40)
                    else:
                        x = random.randrange(650, 1050, 40)
                        y = random.randrange(200, 600 - length, 40)

                # No need to rotate again here
                new_ship = pygame.Rect(x, y, length, 40) if orientation == 'horizontal' else pygame.Rect(x, y, 40, length)
                ship_surface = self.ship_images[ ["Carrier", "Battleship", "Destroyer", "Submarine", "Patrol Boat"].index(name) ]

                # Checks for ship overlap
                overlap = False
                for ship in self.enemy_ships:
                    if new_ship.colliderect(ship["rect"]):
                        overlap = True
                        break

                # Extra spacing for big ships
                if name in ["Carrier", "Battleship"]:
                    for big_ship in big_ships:
                        if new_ship.colliderect(big_ship.inflate(160, 160)):
                            overlap = True
                            break

                if not overlap:
                    # Store ship with orientation info
                    self.enemy_ships.append({
                        "rect": new_ship,
                        "name": name,
                        "health": size,
                        "surface": ship_surface,
                        "orientation": orientation 
                    })

                    if name in ["Carrier", "Battleship"]:
                        big_ships.append(new_ship)
                    else:
                        small_ships.append(new_ship)

                    placed = True

                    # Cluster placement if enabled
                    if cluster_mode and name in ["Destroyer", "Submarine", "Patrol Boat"]:
                        cluster_mode = False  # Only do it once
                        if ships_to_place:
                            cluster_name, cluster_size, cluster_length = ships_to_place.pop(0)

                            # Try to place adjacent to the just placed ship
                            cluster_placed = False
                            attempts = 0
                            while not cluster_placed and attempts < 10:
                                attempts += 1
                                # Randomly pick a side to place nearby
                                direction = random.choice(['up', 'down', 'left', 'right'])

                                if direction == 'right':
                                    cx = new_ship.right
                                    cy = new_ship.top
                                    c_orientation = 'vertical'
                                    c_rect = pygame.Rect(cx, cy, 40, cluster_length)
                                elif direction == 'left':
                                    cx = new_ship.left - 40
                                    cy = new_ship.top
                                    c_orientation = 'vertical'
                                    c_rect = pygame.Rect(cx, cy, 40, cluster_length)
                                elif direction == 'up':
                                    cx = new_ship.left
                                    cy = new_ship.top - cluster_length
                                    c_orientation = 'horizontal'
                                    c_rect = pygame.Rect(cx, cy, cluster_length, 40)
                                elif direction == 'down':
                                    cx = new_ship.left
                                    cy = new_ship.bottom
                                    c_orientation = 'horizontal'
                                    c_rect = pygame.Rect(cx, cy, cluster_length, 40)

                                if (650 <= c_rect.left <= 1050 - 40) and (200 <= c_rect.top <= 600 - 40):
                                    no_overlap = True
                                    for ship in self.enemy_ships:
                                        if c_rect.colliderect(ship["rect"]):
                                            no_overlap = False
                                            break
                                    if no_overlap:
                                        # Pick ship surface
                                        cluster_surface = self.ship_images[ ["Carrier", "Battleship", "Destroyer", "Submarine", "Patrol Boat"].index(cluster_name) ]

                                        self.enemy_ships.append({
                                            "rect": c_rect,
                                            "name": cluster_name,
                                            "health": cluster_size,
                                            "surface": cluster_surface,
                                            "orientation": c_orientation  
                                        })
                                        cluster_placed = True

                            if not cluster_placed:
                                # Couldn't cluster, fallback to normal
                                ships_to_place.insert(0, (cluster_name, cluster_size, cluster_length))

    # Draw the parts of enemy ships that have been hit by the player.
    def draw_enemy_ships(self, surface, reveal=False, attacked_cells=None):
        for ship in self.enemy_ships:
            # reveal mode ON, or ship is fully sunk (health == 0)
            if reveal or ship["health"] == 0:
                ship_surface = ship["surface"]
                ship_rect = ship["rect"]

                # If ship was placed vertically, rotate it back for correct display
                if ship.get("orientation") == "vertical":
                    ship_surface = pygame.transform.rotate(ship_surface, -90)

                surface.blit(ship_surface, ship_rect)

        if attacked_cells:
            for (x, y), result in attacked_cells.items():
                if result == 'Red':
                     # draw explosion at hit cell
                    surface.blit(explosion_image, (x, y)) 


# Reusable button class for menus and interactions
class Button():
    def __init__(self, image, pos, text_input, font, base_color, hovering_color):
        self.text_input = text_input
        self.font = font
        self.base_color = base_color
        self.hovering_color = hovering_color
        self.x_pos = pos[0]
        self.y_pos = pos[1]

        # Render the text surface
        self.text = self.font.render(self.text_input, True, self.base_color)

        padding_x = 40  # horizontal padding around text
        padding_y = 20  # vertical padding around text

        if image is not None:
            # Scale the image to fit the text with padding
            new_width = self.text.get_width() + padding_x
            new_height = self.text.get_height() + padding_y
            self.image = pygame.transform.scale(image, (new_width, new_height))
        else:
            # No image: create a transparent surface as the button background
            self.image = pygame.Surface(
                (self.text.get_width() + padding_x, self.text.get_height() + padding_y),
                pygame.SRCALPHA
            )

        # Get button rectangle centered at position
        self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))

    # Draw the image (if it exists) and text onto the screen at their appropriate positions
    def update(self, screen):
        # Draw background (even if transparent)
        screen.blit(self.image, self.rect)
        # Draw text
        screen.blit(self.text, self.text_rect)

    # Checks if mouse is inside button rectangle
    def checkForInput(self, position):
        return self.rect.collidepoint(position)

    # Changes color of button when hovering over button
    def changeColor(self, position):
        if self.checkForInput(position):
            self.text = self.font.render(self.text_input, True, self.hovering_color)
        else:
            self.text = self.font.render(self.text_input, True, self.base_color)


##Initialize Pygame
pygame.init()

##Create Window
SCREEN = pygame.display.set_mode((1080,1920), pygame.FULLSCREEN)

##Load Menu Background Image from Asset Folder
BG = pygame.image.load("assets/Background.png").convert()
# Load Explosion Image
explosion_image = pygame.image.load("assets/explosion.png").convert_alpha()
explosion_image = pygame.transform.scale(explosion_image, (40, 40))

##Create a reference to font not in assets folder
font = pygame.font.Font(None, 50)


# Checks whether all of the player's ships have been completely destroyed by the enemy
def are_all_player_ships_sunk(player_sprite):
    for ship_rect in player_sprite.defense_ship_rects:
        fully_sunk = True
        for x in range(ship_rect.left, ship_rect.right, 40):
            for y in range(ship_rect.top, ship_rect.bottom, 40):
                if (x, y) not in player_sprite.enemy_attacks or player_sprite.enemy_attacks[(x, y)] != 'Red':
                    fully_sunk = False
                    break
            if not fully_sunk:
                break
        if not fully_sunk:
            return False
    # All ships are fully hit
    return True  


# Returns Press-Start-2P font in the desired size
def get_font(size):
    return pygame.font.Font("assets/font.ttf", size)

# Displays the win screen 
def win_screen(winner, player_sprite, enemy_sprite):
    # Creates a surface to draw the full win screen
    win_surface = pygame.Surface((SCREEN.get_width(), SCREEN.get_height()))
    win_surface.fill('black')

    # Layout variables
    blockSize = 40
    grid_width = blockSize * 10
    spacing_between_grids = 100
    total_width = grid_width * 2 + spacing_between_grids
    start_x = (SCREEN.get_width() - total_width) // 2

    player_grid_start_x = start_x
    player_grid_start_y = 200
    enemy_grid_start_x = start_x + grid_width + spacing_between_grids
    enemy_grid_start_y = 200

    # Title text
    win_text = get_font(100).render(f"{winner} Wins!", True, 'Green')
    win_rect = win_text.get_rect(center=(800, 80))
    win_surface.blit(win_text, win_rect)

    # Grid Labels
    player_label = get_font(40).render("Your Board", True, 'White')
    player_label_rect = player_label.get_rect(center=(player_grid_start_x + grid_width // 2, player_grid_start_y - 40))
    win_surface.blit(player_label, player_label_rect)

    enemy_label = get_font(40).render("Enemy Board", True, 'White')
    enemy_label_rect = enemy_label.get_rect(center=(enemy_grid_start_x + grid_width // 2, enemy_grid_start_y - 40))
    win_surface.blit(enemy_label, enemy_label_rect)

    # Draw player and enemy grids
    for x in range(10):
        for y in range(10):
            player_rect = pygame.Rect(player_grid_start_x + x * blockSize, player_grid_start_y + y * blockSize, blockSize, blockSize)
            enemy_rect = pygame.Rect(enemy_grid_start_x + x * blockSize, enemy_grid_start_y + y * blockSize, blockSize, blockSize)
            pygame.draw.rect(win_surface, 'White', player_rect, 1)
            pygame.draw.rect(win_surface, 'White', enemy_rect, 1)

    # Draw Player Ships
    for ship in player_sprite.defense_ships:
        ship_surface = ship["surface"]
        ship_rect = ship["rect"]
        draw_x = player_grid_start_x + (ship_rect.left - 100)
        draw_y = player_grid_start_y + (ship_rect.top - 200)
        win_surface.blit(ship_surface, (draw_x, draw_y))

    # Draw Enemy Ships
    for ship in enemy_sprite.enemy_ships:
        ship_surface = ship["surface"]
        ship_rect = ship["rect"]

        # If ship was placed vertically, rotate it back for correct display
        if ship.get("orientation") == "vertical":
            rotated_surface = pygame.transform.rotate(ship_surface, -90)
            ship_surface = rotated_surface

        draw_x = enemy_grid_start_x + (ship_rect.left - 650)
        draw_y = enemy_grid_start_y + (ship_rect.top - 200)
        win_surface.blit(ship_surface, (draw_x, draw_y))

    # Draw hit markers on Player board
    for (x, y), color in player_sprite.enemy_attacks.items():
        if color == 'Red':
            hit_x = player_grid_start_x + (x - 100)
            hit_y = player_grid_start_y + (y - 200)
            win_surface.blit(explosion_image, (hit_x, hit_y))

    # Draw hit markers on Enemy board
    for (x, y), color in player_sprite.attacked_cells.items():
        if color == 'Red':
            hit_x = enemy_grid_start_x + (x - 650)
            hit_y = enemy_grid_start_y + (y - 200)
            win_surface.blit(explosion_image, (hit_x, hit_y))

    # Main Menu button
    menu_button_y = enemy_grid_start_y + grid_width + 100
    MENU_BUTTON = Button(image=None, pos=(800, menu_button_y),
                         text_input="MAIN MENU", font=get_font(75),
                         base_color="White", hovering_color="Green")

    # Fade-in effect
    clock = pygame.time.Clock()
    for alpha in range(0, 255, 4):  # Smooth fade
        SCREEN.fill('black')
        temp_surface = win_surface.copy()
        temp_surface.set_alpha(alpha)
        SCREEN.blit(temp_surface, (0, 0))
        pygame.display.update()
        clock.tick(60)

    # Wait for user input
    while True:
        SCREEN.blit(win_surface, (0, 0))

        MOUSE_POS = pygame.mouse.get_pos()
        MENU_BUTTON.changeColor(MOUSE_POS)
        MENU_BUTTON.update(SCREEN)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if MENU_BUTTON.checkForInput(MOUSE_POS):
                    main_menu()

        pygame.display.update()

# Main Gameloop after ship placement
def begin(player_sprite):
    player_sprites = pygame.sprite.Group(player_sprite)
    enemy_sprite = EnemyShipSprite()
    enemy_sprites = pygame.sprite.Group(enemy_sprite)

    # Initialize ai hunting algorithm
    initialize_enemy_hunt_targets()

    # Shift player ships from placement game board
    player_sprite.defense_ships = []
    for surface, rect in zip(player_sprite.ship_init_surface, player_sprite.ship_init_rect):
        new_rect = rect.copy()
        new_rect.x = new_rect.x - 250  
        player_sprite.defense_ships.append({
            "surface": surface,
            "rect": new_rect
        })

    # Update the defense_ship_rects list so AI knows the player ships
    player_sprite.defense_ship_rects = [ship["rect"] for ship in player_sprite.defense_ships] 
    
    player_turn = True

    # Game loop
    while True:
        OPTIONS_MOUSE_POS = pygame.mouse.get_pos()
        SCREEN.fill("black")

        # Event Handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Check player attack
            if player_turn and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                shot_successful = player_sprite.attack_phase(event, enemy_sprite)
                if shot_successful:
                    # Check if player won after attack
                    if all(ship["health"] == 0 for ship in enemy_sprite.enemy_ships):
                        fade_to_win_screen("Player", player_sprite, enemy_sprite)
                    player_turn = False

        # Enemy Turn
        if not player_turn:
            pygame.time.delay(500)
            enemy_shoot(player_sprite)
            # Check if enemy won after their attack
            if are_all_player_ships_sunk(player_sprite):
                fade_to_win_screen("Enemy", player_sprite, enemy_sprite)
            player_turn = True

        # Draw boards/screen
        grid2()
        player_sprites.draw(SCREEN)
        enemy_sprite.draw_enemy_ships(SCREEN, reveal=False, attacked_cells=player_sprite.attacked_cells)

        player_sprite.draw_ship_offset(SCREEN)
        player_sprite.draw_attacked_cells(SCREEN)  # player's attacks on enemy
        player_sprite.draw_enemy_attacks(SCREEN)   # enemy attacks on player
        player_sprite.draw_attack_text(SCREEN)

        pygame.display.update()


# Ship Placement gameloop
def play():
    ##Create Reference to sprites
    sprite = AllShipSprite(None, (0, 0))
    all_sprites = pygame.sprite.Group(sprite)

    # Allows for ships to change position
    move_ships = True 

    # Gameloop for ship placement
    while True:
        # Get Mouse Position
        PLAY_MOUSE_POS = pygame.mouse.get_pos()
        # Constantly black background
        SCREEN.fill('Black')  

        # Event handler
        for event in pygame.event.get():  
            #allows for closing window
            if event.type == pygame.QUIT:  
                pygame.quit() 
                sys.exit() 
            
            #Ships being moved
            if move_ships == True:
                # rotate the active ship if button is pressed
                sprite.rotate_ship(event)   
                # dragging ship
                sprite.drag_ship(event)  
                # clear the grid by returning ships back
                sprite.return_ship(event)  
           
            #Back Button
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PLAY_BACK.checkForInput(PLAY_MOUSE_POS):
                    main_menu()
            # Checks if all ships are placed
            if are_all_ships_placed(sprite) == True: 
                # Stops you from editing the ship's position
                if event.type == pygame.MOUSEBUTTONDOWN: 
                    if PLAY_CONFIRM.checkForInput(PLAY_MOUSE_POS):
                        # Stops you from editing the ship's position
                        move_ships = False 
                        return sprite
                       


                     
        # draw the grid
        grid()  
        # draw all sprites
        all_sprites.draw(SCREEN)  
        sprite.draw_ship(SCREEN, show_ships=move_ships)
        # Draws buttons only if ship position can be changed
        if move_ships == True: 
            sprite.draw_rotate_button(SCREEN) 
            sprite.draw_clear_button(SCREEN) 
            sprite.draw_instruction_text(SCREEN) 
            sprite.draw_title_text(SCREEN)  
        # Draws buttons only if ship position cannot be changed
        if move_ships == False: 
            # draw the attacked cells
            sprite.draw_attacked_cells(SCREEN) 
            sprite.draw_attack_text(SCREEN)  
           
       
        ##Back Button
        PLAY_BACK = Button(image=None, pos=(1200, 460),
                            text_input="BACK", font=get_font(75), base_color="White", hovering_color="Green")
        PLAY_BACK.changeColor(PLAY_MOUSE_POS)
        PLAY_BACK.update(SCREEN)

        # Confirm Button
        if are_all_ships_placed(sprite) == True:
            PLAY_CONFIRM = Button(image=None, pos=(1200, 260), text_input="Confirm", font=get_font(75),
                              base_color="White", hovering_color="Green")
            PLAY_CONFIRM.changeColor(PLAY_MOUSE_POS)
            PLAY_CONFIRM.update(SCREEN)

        pygame.display.update()


# Instructions Button
def instructions():
    # Display instructions
    while True:
        # dark blue background
        SCREEN.fill('Navy')  

        # Instructions
        INSTRUCTIONS_TITLE = get_font(80).render("HOW TO PLAY", True, "White")
        INSTRUCTIONS_TEXT1 = get_font(30).render("Place your ships on the grid and confirm to play.", True, "White")
        INSTRUCTIONS_TEXT2 = get_font(30).render("Attack the enemy grid which is on the right.", True, "White")
        INSTRUCTIONS_TEXT3 = get_font(30).render("Sink all 5 enemy ships to win!", True, "White")

        #Back button
        BACK_BUTTON = Button(image=None, pos=(800, 800), text_input="BACK", font=get_font(75),
                              base_color="White", hovering_color="Green")

        # Instruction label positions
        SCREEN.blit(INSTRUCTIONS_TITLE, INSTRUCTIONS_TITLE.get_rect(center=(800, 150)))
        SCREEN.blit(INSTRUCTIONS_TEXT1, INSTRUCTIONS_TEXT1.get_rect(center=(800, 300)))
        SCREEN.blit(INSTRUCTIONS_TEXT2, INSTRUCTIONS_TEXT2.get_rect(center=(800, 400)))
        SCREEN.blit(INSTRUCTIONS_TEXT3, INSTRUCTIONS_TEXT3.get_rect(center=(800, 500)))

        #mouse position
        MOUSE_POS = pygame.mouse.get_pos()

        # back button updates
        BACK_BUTTON.changeColor(MOUSE_POS)
        BACK_BUTTON.update(SCREEN)

        # Event Handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if BACK_BUTTON.checkForInput(MOUSE_POS):
                    main_menu()

        pygame.display.update()




# Main Menu
def main_menu():
    #Initial background image x
    x = 0
    # Background Movement loop
    while True:
        ##Set background image to screen
        relative_x = x % BG.get_rect().width
        SCREEN.blit(BG, (relative_x - BG.get_rect().width, -50))
        #Move Background image across screen
        if relative_x < 3840:
             SCREEN.blit(BG, (relative_x, -50))
        x -= .25

        ##Get Mouse Position
        MENU_MOUSE_POS = pygame.mouse.get_pos()

        ##Set Title
        MENU_TEXT = get_font(100).render("BATTLESHIP", True, "#b68f40")
        MENU_RECT = MENU_TEXT.get_rect(center=(800, 100))

        ##Create Menu Buttons
        PLAY_BUTTON = Button(image=pygame.image.load("assets/Play Rect.png"), pos=(800, 250),
                            text_input="PLAY", font=get_font(75), base_color="#d7fcd4", hovering_color="White")
        INSTRUCTIONS_BUTTON = Button(image=pygame.image.load("assets/Options Rect.png"), pos=(800, 400),
                            text_input="Instructions", font=get_font(75), base_color="#d7fcd4", hovering_color="White")
        QUIT_BUTTON = Button(image=pygame.image.load("assets/Quit Rect.png"), pos=(800, 550),
                            text_input="QUIT", font=get_font(75), base_color="#d7fcd4", hovering_color="White")

        SCREEN.blit(MENU_TEXT, MENU_RECT)

        ##Cycles through buttons for screen updates
        for button in [PLAY_BUTTON, INSTRUCTIONS_BUTTON, QUIT_BUTTON]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(SCREEN)
       
        ##Event handler
        for event in pygame.event.get():
            #Quit
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            #Call associated function with button
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PLAY_BUTTON.checkForInput(MENU_MOUSE_POS):
                    sprite = play()
                    if sprite:
                        begin(sprite)
                if INSTRUCTIONS_BUTTON.checkForInput(MENU_MOUSE_POS):
                    instructions()
                if QUIT_BUTTON.checkForInput(MENU_MOUSE_POS):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()

# Draw two grids: one for player ships, one for attacking
def grid2():
    blockSize = 40
    # Player's grid (left)
    for x in range(100, 500, blockSize):  
        for y in range(200, 600, blockSize):
            rect = pygame.Rect(x, y, blockSize, blockSize)
            pygame.draw.rect(SCREEN, 'White', rect, 1)
    # Attack grid (right)
    for x in range(650, 1050, blockSize):  
        for y in range(200, 600, blockSize):
            rect = pygame.Rect(x, y, blockSize, blockSize)
            pygame.draw.rect(SCREEN, 'White', rect, 1)

# Draw grid for placing ships
def grid():
    blockSize = 40
    for x in range(350, 750, blockSize):  
        for y in range(200, 600, blockSize):  
            rect = pygame.Rect(x, y, blockSize, blockSize)  
            pygame.draw.rect(SCREEN, 'White', rect, 1)   



# Class for managing player ships
class AllShipSprite(pygame.sprite.Sprite):  
    # initialize the class
    def __init__(self, image, pos):
        super().__init__()
        self.image = pygame.Surface((1000, 800), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=pos)

        self.defense_ship_rects = []

        # create the ships and load assets
        self.carrier = pygame.image.load("assets/carrier.png").convert_alpha()
        self.carrier = pygame.transform.scale(self.carrier, (40, 200))

        self.battleship = pygame.image.load("assets/battleship.png").convert_alpha()
        self.battleship = pygame.transform.scale(self.battleship, (40, 160))

        self.destroyer = pygame.image.load("assets/destroyer.png").convert_alpha()
        self.destroyer = pygame.transform.scale(self.destroyer, (40, 120))

        self.submarine = pygame.image.load("assets/submarine.png").convert_alpha()
        self.submarine = pygame.transform.scale(self.submarine, (40, 120))

        self.patrolboat = pygame.image.load("assets/patrolboat.png").convert_alpha()
        self.patrolboat = pygame.transform.scale(self.patrolboat, (40, 80))

        # list of all ships surfaces
        self.ship_init_surface = [self.carrier, self.battleship, self.destroyer, self.submarine, self.patrolboat]
        self.ship_init_surface_copy = [self.carrier, self.battleship, self.destroyer, self.submarine, self.patrolboat]  # copy

        # list of all ships rectangles
        self.ship_init_rect = [
            self.carrier.get_rect(topleft=(200, 200), width=40, height=200),  # create rectangle for these ships
            self.battleship.get_rect(topleft=(120, 200), width=40, height=160),
            self.destroyer.get_rect(topleft=(200, 440), width=40, height=120),
            self.submarine.get_rect(topleft=(120, 400), width=40, height=120),
            self.patrolboat.get_rect(topleft=(120, 560), width=40, height=80)
        ]
        self.ship_init_rect_copy = [
            self.carrier.get_rect(topleft=(200, 200), width=40, height=200),  # copy
            self.battleship.get_rect(topleft=(120, 200), width=40, height=160),
            self.destroyer.get_rect(topleft=(200, 440), width=40, height=120),
            self.submarine.get_rect(topleft=(120, 400), width=40, height=120),
            self.patrolboat.get_rect(topleft=(120, 560), width=40, height=80)
        ]

        # initialize variable to store selected ship and initialize the related datas
        self.active_ship = None
        self.selected_index = 0
        self.center = None

        # create shadow to preview dropping ship
        self.shadow_rect = pygame.Rect(0, 0, 0, 0)
        self.shadow_surface = pygame.Surface((self.shadow_rect.width, self.shadow_rect.height), pygame.SRCALPHA)
        self.shadow_surface.fill((0, 255, 0, 70))  # green with 70% transparency

        # create the rotate button
        self.rotate_rect = pygame.Rect(825, 200, 100, 100)  # create a rect to draw
        self.rotate_text = font.render('R', True, 'White')  # create a text 'R' meaning rotate
        self.rotate_text_rect = self.rotate_text.get_rect(center=self.rotate_rect.center)  # create a rect to define position to draw
       
        # create the clear button
        self.clear_rect = pygame.Rect(825, 400, 100, 100)  # create a rect to draw
        self.clear_text = font.render('C', True, 'White')  # create a text 'C' meaning clear the grid
        self.clear_text_rect = self.clear_text.get_rect(center=self.clear_rect.center)  # create a rect to define position to draw

        # create the title text
         # create a title text as 'Place Your Ships'
        self.title_text = font.render('Place all ships within the grid. Select confirm to continue.', True, 'White') 
         # create a rect to define position to draw
        self.title_text_rect = self.title_text.get_rect(topleft=(100, 100), width=900, height=50) 

        # create the instruction text
        # create a title text as 'Click \'R\' to rotate;\nClick \'C\' to clear the board.'
        self.instruction_text = font.render("Click 'R' to rotate ships; Click 'C' to clear the board." , True, 'White')  
        # create a rect to define position to draw
        self.instruction_text_rect = self.title_text.get_rect(topleft=(200, 700), width=900, height=100)  
       
        self.attacked_cells = {} # list to store the attacked cells      
        self.enemy_attacks = {}  # stores enemy attacks on player's ships
        self.sunk_ships = [] # tracks ships player has sunk

    # draw the rotate\clear\title\instruction\confirm button
    def draw_rotate_button(self, surface):
        pygame.draw.rect(SCREEN, 'White', self.rotate_rect, 1)  # draw the botton as rect defined
        self.image.blit(self.rotate_text, self.rotate_text_rect)  # draw the text rect on the botton rect

    def draw_clear_button(self, surface):
        pygame.draw.rect(SCREEN, 'White', self.clear_rect, 1)  # draw the botton as rect defined
        self.image.blit(self.clear_text, self.clear_text_rect)  # draw the text rect on the botton rect

    def draw_title_text(self, surface):
        self.image.blit(self.title_text, self.title_text_rect)  # draw the text on the text rect

    def draw_instruction_text(self, surface):
        self.image.blit(self.instruction_text, self.instruction_text_rect)  # draw the text on the text rect


    # Draws the ships on their original placement grid
    def draw_ship(self, surface, show_ships=True):
        self.image.fill((255, 255, 255, 0))  # [color:transparent] background
        self.image.blit(self.shadow_surface, self.shadow_rect)
        if show_ships:  # Only draw ships if show_ships is True
            for ship_surface, ship_rect in zip(self.ship_init_surface, self.ship_init_rect):
                self.image.blit(ship_surface, ship_rect)

    def draw_ship_offset(self, surface, show_ships=True):
        self.image.fill((255, 255, 255, 0))  # transparent background
        self.image.blit(self.shadow_surface, self.shadow_rect)
        if show_ships:
            for ship_surface, ship_rect in zip(self.ship_init_surface, self.ship_init_rect):
                offset_rect = ship_rect.copy()
                offset_rect.x -= 250 
                self.image.blit(ship_surface, offset_rect)

    # mouse drag and drop ships
    def drag_ship(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for num, box in enumerate(self.ship_init_rect):
                if box.collidepoint(event.pos):
                    self.active_ship = self.ship_init_rect[num]
                    self.selected_index = int(num)
                    self.center = self.active_ship.center

        elif event.type == pygame.MOUSEMOTION:
            if self.active_ship != None:
                self.active_ship.move_ip(event.rel)

                # move the shadow while dragging through mouse
                grid_x = round((self.active_ship.x - 350) / 40) * 40 + 350
                grid_y = round((self.active_ship.y - 200) / 40) * 40 + 200

                self.shadow_rect = self.active_ship.copy()
                self.shadow_rect.topleft = (grid_x, grid_y)

                # Define the board boundaries
                board_rect = pygame.Rect(350, 200, 400, 400)

                if board_rect.contains(self.shadow_rect):
                    # Check if shadow overlaps with other ships
                    conflict = False
                    for i, other_ship in enumerate(self.ship_init_rect):
                        if i != self.selected_index and self.shadow_rect.colliderect(other_ship):
                            conflict = True
                            break

                    self.shadow_surface = pygame.Surface((self.shadow_rect.width, self.shadow_rect.height), pygame.SRCALPHA)
                    if conflict:
                        self.shadow_surface.fill((255, 0, 0, 120))  # Red transparent for conflict
                    else:
                        self.shadow_surface.fill((0, 255, 0, 120))  # Green transparent for valid
                else:
                    self.shadow_surface = pygame.Surface((self.shadow_rect.width, self.shadow_rect.height), pygame.SRCALPHA)
                    self.shadow_surface.fill((0, 0, 0, 0))  # Fully transparent (no shadow)

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.active_ship != None:
                board_rect = pygame.Rect(350, 200, 400, 400)

                grid_x = round((self.active_ship.x - 350) / 40) * 40 + 350
                grid_y = round((self.active_ship.y - 200) / 40) * 40 + 200


                if (grid_x >= 350 and grid_x + self.active_ship.width <= 750 and
                    grid_y >= 200 and grid_y + self.active_ship.height <= 600):


                    conflict = False
                    for i, other_ship in enumerate(self.ship_init_rect):
                        if i != self.selected_index and self.shadow_rect.colliderect(other_ship):
                            conflict = True
                            break


                    if not conflict:
                        self.active_ship.topleft = (grid_x, grid_y)
                    else:
                        self.active_ship.topleft = self.ship_init_rect_copy[self.selected_index].topleft
                else:
                    self.active_ship.topleft = self.ship_init_rect_copy[self.selected_index].topleft


                self.shadow_surface.fill((255, 255, 255, 0))
                self.active_ship = None

    # rotate the ships
    def rotate_ship(self, event):
        # Click button 'R' to rotate
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rotate_rect.collidepoint(event.pos):
                self.perform_rotation()
        # Use spacebar as alternative rotate
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.perform_rotation()

    # Handler for rotating Ships
    def perform_rotation(self):
        if self.selected_index is not None:
            current_ship_surface = self.ship_init_surface[self.selected_index]
            current_ship_rect = self.ship_init_rect[self.selected_index]

            mouse_x, mouse_y = pygame.mouse.get_pos()

            # Calculate offset before rotation
            offset_x = mouse_x - current_ship_rect.left
            offset_y = mouse_y - current_ship_rect.top

            old_topleft = current_ship_rect.topleft
            old_topright = current_ship_rect.topright
            old_bottomleft = current_ship_rect.bottomleft

            # Rotate the current ship surface
            rotated_ship_surface = pygame.transform.rotate(current_ship_surface, 90)
            rotated_ship_rect = rotated_ship_surface.get_rect()

            if (current_ship_rect.x + current_ship_rect.height <= 750 and current_ship_rect.y + current_ship_rect.width <= 600):
                rotated_ship_rect.topleft = old_topleft
            elif current_ship_rect.x + current_ship_rect.height >= 750:
                rotated_ship_rect.topright = old_topright
            elif current_ship_rect.y + current_ship_rect.width >= 600:
                rotated_ship_rect.bottomleft = old_bottomleft

            # Check for conflicts
            conflict = False
            for i, other_ship in enumerate(self.ship_init_rect):
                if i != self.selected_index and rotated_ship_rect.colliderect(other_ship):
                    conflict = True
                    break

            if not conflict:
                self.ship_init_rect[self.selected_index] = rotated_ship_rect
                self.ship_init_surface[self.selected_index] = rotated_ship_surface

                if self.active_ship is not None:
                    # Attempt to preserve rotation in relation to mouse using offsets
                    new_left = mouse_x - offset_x
                    new_top = mouse_y - offset_y
                    self.active_ship = rotated_ship_rect
                    self.active_ship.topleft = (new_left, new_top)

                self.shadow_rect = rotated_ship_rect.copy()
                self.shadow_surface = pygame.Surface((self.shadow_rect.width, self.shadow_rect.height), pygame.SRCALPHA)
                self.shadow_surface.fill((0, 255, 0, 120))

                self.draw_ship(SCREEN)
           

    # clear the grid = return all ships to initial position
    def return_ship(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.clear_rect.collidepoint(event.pos):
                # Reset all ship positions and rotations
                for i in range(len(self.ship_init_rect)):
                    self.ship_init_rect[i] = self.ship_init_rect_copy[i].copy()
                    self.ship_init_surface[i] = self.ship_init_surface_copy[i]
                self.active_ship = None
                self.selected_index = 0
                self.center = None
   
   #Determines logic for attacking enemy grid
    def attack_phase(self, event, enemy_sprite):
        # Determine attack cell
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            attack_grid_rect = pygame.Rect(650, 200, 400, 400)
            if attack_grid_rect.collidepoint(mouse_pos):
                grid_x = (mouse_pos[0] - 650) // 40 * 40 + 650
                grid_y = (mouse_pos[1] - 200) // 40 * 40 + 200
                cell_key = (grid_x, grid_y)

                if cell_key in self.attacked_cells:
                    return False  # already attacked

                clicked_rect = pygame.Rect(grid_x, grid_y, 40, 40)

                hit = False
                # Enemy ship health for tracking win condition/enemy ship type for display
                for ship in enemy_sprite.enemy_ships:
                    if clicked_rect.colliderect(ship["rect"]):
                        hit = True
                        ship["health"] -= 1
                        if ship["health"] == 0:
                            self.sunk_ships.append(ship["name"])  # Save the name to show!
                        break

                self.attacked_cells[cell_key] = 'Red' if hit else 'White'
                return True
        return False
   
   # Draws explosion for hit, white circle for miss
    def draw_attacked_cells(self, surface):
        for (x, y), color in self.attacked_cells.items():
            if color == 'Red':
                # Draw explosion sprite at hit location
                surface.blit(explosion_image, (x, y))
            else:
                # Draw white circle for misses
                center_x = x + 20  # Center of the cell (x + half cell width)
                center_y = y + 20  # Center of the cell (y + half cell height)
                pygame.draw.circle(surface, 'White', (center_x, center_y), 15)
   
    # Draw the enemy's attacks on the player's grid (left grid)
    def draw_enemy_attacks(self, surface):
        for (x, y), result in self.enemy_attacks.items():
            if result == 'Red':
                surface.blit(explosion_image, (x, y))  # draw explosion at hit cell
            else:
                center_x = x + 20
                center_y = y + 20
                pygame.draw.circle(surface, 'White', (center_x, center_y), 15)  # draw white circle for miss

    # Draw text instructions during attack phase
    def draw_attack_text(self, surface):
        attack_text = font.render('Attack Phase: Click grid to fire!', True, 'White')
        attack_text_rect = attack_text.get_rect(topleft=(350, 150), width=400, height=40)
        surface.blit(attack_text, attack_text_rect) 


        # Draw all sunk ships vertically
        start_y = 180  
        for index, ship_name in enumerate(self.sunk_ships):
            sunk_text = font.render(f"You sank the {ship_name}!", True, 'Green')
            sunk_text_rect = sunk_text.get_rect(topleft=(1100, start_y + index * 40))  #shifted left, spaced vertically
            surface.blit(sunk_text, sunk_text_rect)


#Check if all ships are placed within the grid.
def are_all_ships_placed(sprite):
    grid_rect = pygame.Rect(350, 200, 400, 400)  # Define the grid boundaries
    for ship_rect in sprite.ship_init_rect:
        if not grid_rect.contains(ship_rect):  # Check if the ship is fully within the grid
            return False  # If any ship is outside the grid, return False
    return True  # All ships are within the grid


# Initialize enemy hunt targets with even spread.
def initialize_enemy_hunt_targets():
    global enemy_hunt_targets
    enemy_hunt_targets = []

    for x in range(100, 500, 40):
        for y in range(200, 600, 40):
            # Only checkerboard cells for search pattern
            if ((x - 100) // 40 + (y - 200) // 40) % 2 == 0:
                enemy_hunt_targets.append((x, y))
    # randomize
    random.shuffle(enemy_hunt_targets)  

# Control's ai behavior by determining attack mode
def enemy_shoot(player_sprite):
    global enemy_ai_state
    global enemy_hunt_targets

    # Hunt mode for searching for ships
    if enemy_ai_state["mode"] == "hunt":
        while enemy_hunt_targets:
            grid_x, grid_y = enemy_hunt_targets.pop()
            cell_key = (grid_x, grid_y)

            # Check if cell has already been shot
            if cell_key not in player_sprite.enemy_attacks:
                clicked_rect = pygame.Rect(grid_x, grid_y, 40, 40)

                # Check for ship
                hit = False
                for ship_rect in player_sprite.defense_ship_rects:
                    if clicked_rect.colliderect(ship_rect):
                        hit = True
                        break

                # Hit or miss state marker
                player_sprite.enemy_attacks[cell_key] = 'Red' if hit else 'White'

                # Switch to target mode after hitting a ship
                if hit:
                    enemy_ai_state["mode"] = "target"
                    # first hit position
                    enemy_ai_state["first_hit_pos"] = (grid_x, grid_y)
                    # attack around first position
                    enemy_ai_state["target_queue"] = [
                        (grid_x + 40, grid_y),
                        (grid_x - 40, grid_y),
                        (grid_x, grid_y + 40),
                        (grid_x, grid_y - 40),
                    ]
                    enemy_ai_state["target_direction"] = None
                break
        else:
            enemy_ai_state["mode"] = "target"  # fallback for no hunt target

    # In target mode
    elif enemy_ai_state["mode"] == "target":
        while enemy_ai_state["target_queue"]:
            # select attack target
            tx, ty = enemy_ai_state["target_queue"].pop(0)

            # check hit is in board
            if 100 <= tx < 500 and 200 <= ty < 600:
                cell_key = (tx, ty)

                # check if already shot
                if cell_key not in player_sprite.enemy_attacks:
                    clicked_rect = pygame.Rect(tx, ty, 40, 40)
                
                    hit = False
                    # Shoot
                    for ship_rect in player_sprite.defense_ship_rects:
                        if clicked_rect.colliderect(ship_rect):
                            hit = True
                            break

                    player_sprite.enemy_attacks[cell_key] = 'Red' if hit else 'White'


                    if hit:
                        # Determine shooting direction
                        if enemy_ai_state["target_direction"] is None:
                            # based on first hit
                            fx, fy = enemy_ai_state["first_hit_pos"]
                            if tx == fx:
                                enemy_ai_state["target_direction"] = "vertical"
                            elif ty == fy:
                                enemy_ai_state["target_direction"] = "horizontal"

                        # Continue in the locked direction
                        if enemy_ai_state["target_direction"] == "horizontal":
                            enemy_ai_state["target_queue"].insert(0, (tx + 40, ty))
                            enemy_ai_state["target_queue"].insert(0, (tx - 40, ty))
                        elif enemy_ai_state["target_direction"] == "vertical":
                            enemy_ai_state["target_queue"].insert(0, (tx, ty + 40))
                            enemy_ai_state["target_queue"].insert(0, (tx, ty - 40))
                    else:
                        if not enemy_ai_state["target_queue"]:
                            enemy_ai_state["mode"] = "hunt"
                    break
        else:
            enemy_ai_state["mode"] = "hunt"
            enemy_ai_state["first_hit_pos"] = None
            enemy_ai_state["target_direction"] = None
            # Immediately hunt again
            enemy_shoot(player_sprite)  


# fade for winscreen
def fade_to_win_screen(winner, player_sprite, enemy_sprite):
    clock = pygame.time.Clock()
    fade_surface = pygame.Surface((SCREEN.get_width(), SCREEN.get_height()))
    fade_surface.fill((0, 0, 0))


    # Draw the final frame (game state frozen)
    SCREEN.fill('black')
    grid2()
    player_sprite.draw_ship_offset(SCREEN)
    player_sprite.draw_attacked_cells(SCREEN)
    player_sprite.draw_enemy_attacks(SCREEN)
    pygame.display.update()


    # Fade smoothly
    for alpha in range(0, 255, 4):  # smaller step for smoother fade
        fade_surface.set_alpha(alpha)
        SCREEN.blit(fade_surface, (0, 0))
        pygame.display.update()
        clock.tick(60)  # 60 FPS cap
   
    win_screen(winner, player_sprite, enemy_sprite)

# Screen for placing ships
def place_ships(sprite, text):
    all_sprites = pygame.sprite.Group(sprite)
    move_ships = True

    # Confirm ship positions button
    PLAY_CONFIRM = Button(image=None, pos=(1200, 260), text_input="Confirm", font=get_font(75),
                           base_color="White", hovering_color="Green")

    # Ship placement gameloop
    while True:
        SCREEN.fill('Black')
        PLAY_MOUSE_POS = pygame.mouse.get_pos()

        # Move this AFTER we get mouse position each frame
        PLAY_CONFIRM.changeColor(PLAY_MOUSE_POS)
        PLAY_CONFIRM.update(SCREEN)

        # Event Handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            #Ship movement
            if move_ships:
                sprite.rotate_ship(event)
                sprite.drag_ship(event)
                sprite.return_ship(event)
            # Confirm Placement
            if event.type == pygame.MOUSEBUTTONDOWN:
                if are_all_ships_placed(sprite) and PLAY_CONFIRM.checkForInput(PLAY_MOUSE_POS):
                    move_ships = False
                    return

        # Draw everything
        grid()
        all_sprites.draw(SCREEN)
        sprite.draw_ship(SCREEN, show_ships=move_ships)
        # placement UI
        if move_ships:
            sprite.draw_rotate_button(SCREEN)
            sprite.draw_clear_button(SCREEN)
            sprite.draw_instruction_text(SCREEN)
            sprite.draw_title_text(SCREEN)

        pygame.display.update()

###Call main menu when game is started
main_menu()
