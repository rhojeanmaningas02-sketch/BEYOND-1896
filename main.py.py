import pygame
import sys

# Initialize Pygame (works in browser!)
pygame.init()

# Set up the screen (adjust this if your game is bigger/smaller)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Your Game Name") # CHANGE THIS to your actual game name!

# Game loop (this runs your game)
running = True
while running:
    # Handle when someone closes the game window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Fill the screen with a color (like white, or change this to a color you want)
    screen.fill((255, 255, 255))

    # --- THIS IS WHERE YOU ADD YOUR ACTUAL GAME CODE! ---
    # If you have sprites, characters, or other parts of your game, put them here!
    # For example: if you have a player, draw it here.

    # Update the screen to show everything
    pygame.display.flip()

# Close the game properly
pygame.quit()
sys.exit()
