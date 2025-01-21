import pygame
from Buttons.buttons import Button
from PIL import Image, ImageFilter

class Popup:
    def __init__(self, name, screen, text, theme_color, button_text, visible, max_line_length=35, font_size=30):
        """
        Initialize the Popup object.

        Args:
            name (str): The name of the popup
            screen (pygame.Surface): The screen surface where the popup will be displayed.
            text (str): The message text for the popup.
            theme_color (str): The hex color code for the popup background and button.
            button_text (str): The text to display on the OK button.
            max_line_length (int): Maximum character length for each line of text.
            visible (bool): Should the platform be visible yet or not.
            font_size (int): The font size for the text to be displayed in.
        """
        self.name = name
        self.screen = screen
        self.text = text
        self.theme_color = theme_color
        self.button_text = button_text
        self._font_size = font_size
        self.font = pygame.font.Font('fonts/pixelated.ttf', self._font_size)  # Font for the popup text
        self.max_line_length = max_line_length  # Maximum character length per line
        # Create the button
        self.button = Button(image=None, pos=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 165),
                             text_input=self.button_text,
                             font=self.font,
                             base_color=self.theme_color,
                             hovering_color="#F59071")
        self.visible = bool(visible)

    @property
    def font_size(self):
        return self._font_size

    @font_size.setter
    def font_size(self, value):
        self._font_size = value
        self.font = pygame.font.Font('fonts/pixelated.ttf', self._font_size)
    
    def draw(self):
        """Draw the popup on the screen."""
        if self.visible:
            self._draw_blurred_background()
            self._draw_text()
            self.button.changeColor(pygame.mouse.get_pos())
            self.button.update(self.screen)

    def _draw_blurred_background(self):
        """Draw a blurred background behind the popup."""
        popup_rect = pygame.Rect(self.screen.get_width() // 2 - 400, self.screen.get_height() // 2 - 100, 800, 300)
        
        # Create an off-screen surface to apply Gaussian blur
        background_surface = pygame.Surface((popup_rect.width, popup_rect.height), pygame.SRCALPHA)
        background_surface.fill((0, 0, 0, 200))  # Semi-transparent black background
        
        # Apply Gaussian blur using PIL
        image_pil = Image.frombytes('RGBA', background_surface.get_size(), pygame.image.tostring(background_surface, 'RGBA'))
        blurred_image_pil = image_pil.filter(ImageFilter.GaussianBlur(6))  # Adjust the blur intensity
        background_surface = pygame.image.fromstring(blurred_image_pil.tobytes(), blurred_image_pil.size, 'RGBA')

        # Blit the blurred background surface
        self.screen.blit(background_surface, popup_rect.topleft)

    def _draw_text(self):
        """Render and draw the popup text with line breaks if necessary."""
        lines = self._split_text_into_lines(self.text, self.max_line_length)
        line_spacing = 10
        y_offset = self.screen.get_height() // 2 - 50  # Starting y position for the first line

        for line in lines:
            text_surface = self.font.render(line, True, '#FFFFFF')  # White text
            text_rect = text_surface.get_rect(center=(self.screen.get_width() // 2, y_offset))
            self.screen.blit(text_surface, text_rect)
            y_offset += text_rect.height + line_spacing

    def _split_text_into_lines(self, text, max_length):
        """Split the text into lines based on max length."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) <= max_length:
                current_line.append(word)
                current_length += len(word) + 1  # +1 for space
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def handle_event(self, event):
        """Handle the button click event."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.button.checkForInput(pygame.mouse.get_pos()):
                self.visible = False  # Close the popup when the button is clicked

    def update(self):
        """Update the popup display."""
        if self.visible:
            self.draw()
