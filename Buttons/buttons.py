class Button():

    def __init__(self, image, pos, font, base_color, hovering_color, text_input):
        self.image = image
        self.x_coordinate = pos[0]
        self.y_coordinate = pos[1]
        self.font = font
        self.base_color, self.hovering_color = base_color, hovering_color
        self.text_input = text_input
        self.text = self.font.render(self.text_input, True, self.base_color)

        if self.image is None:
            self.image = self.text
        
        elif self.text_input is None:
            self.text = self.image

        self.rect = self.image.get_rect(center=(self.x_coordinate, self.y_coordinate))
        self.text_rect = self.text.get_rect(center=(self.x_coordinate, self.y_coordinate))

    def update(self, screen):
        
        if self.image is not None:
            screen.blit(self.image, self.rect)
        
        screen.blit(self.text, self.text_rect)
    
    def checkForInput(self, position):

        if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
            return True
        return False
    
    def changeColor(self, position):

        if self.checkForInput(position):
            self.text = self.font.render(self.text_input, True, self.hovering_color)
        
        else:
            self.text = self.font.render(self.text_input, True, self.base_color)