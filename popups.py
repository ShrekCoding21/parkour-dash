import pygame
from Buttons.buttons import Button
from PIL import Image, ImageFilter

class Popup:
    def __init__(self, screen, text, theme_color, button_text, max_line_length=40):
        """
        Initialize the Popup object.

        Args:
            screen (pygame.Surface): The screen surface where the popup will be displayed.
            text (str): The message text for the popup.
            theme_color (str): The hex color code for the popup background and button.
            button_text (str): The text to display on the OK button.
            max_line_length (int): Maximum character length for each line of text.
        """
        self.screen = screen
        self.text = text
        self.theme_color = theme_color
        self.button_text = button_text
        self.font = pygame.font.Font('fonts/MajorMonoDisplay-Regular.ttf', 30)  # Font for the popup text
        self.max_line_length = max_line_length  # Maximum character length per line

        # Create the button
        self.button = Button(image=None, pos=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 100),
                             text_input=self.button_text,
                             font=self.font,
                             base_color=self.theme_color,
                             hovering_color="#F59071")
        self.visible = True

    def draw(self):
        """Draw the popup on the screen."""
        if self.visible:
            self._draw_blurred_background()
            self._draw_text()
            self.button.update(self.screen)

    def _draw_blurred_background(self):
        """Draw a blurred background behind the popup."""
        popup_rect = pygame.Rect(self.screen.get_width() // 2 - 200, self.screen.get_height() // 2 - 100, 400, 200)
        
        # Create an off-screen surface to apply Gaussian blur
        background_surface = pygame.Surface((popup_rect.width, popup_rect.height), pygame.SRCALPHA)
        background_surface.fill((0, 0, 0, 128))  # Semi-transparent black background
        
        # Apply Gaussian blur using PIL
        image_pil = Image.frombytes('RGBA', background_surface.get_size(), pygame.image.tostring(background_surface, 'RGBA'))
        blurred_image_pil = image_pil.filter(ImageFilter.GaussianBlur(10))  # Adjust the blur intensity
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
