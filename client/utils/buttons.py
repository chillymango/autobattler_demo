"""
Helpers for buttons
"""
from PyQt5.QtWidgets import QPushButton

TRANSPARENT_IMAGE = '{}'


def clear_button_image(button):
    """
    Reset the button image
    """
    button.setStyleSheet("border: 1px solid;")


def set_button_image(button, image, color):
    """
    Set a scaled image with background color
    """
    button.setStyleSheet(
        "border-image: url('{image}');"
        "background-color: {color};"
        .format(image=image, color=color)
    )


def set_border_color(button: QPushButton, color: str, width: int = 5) -> None:
    """
    Set a border and a color
    """
    button.setStyleSheet(
        "border: {width}px solid;"
        "border-top-color: {color};"
        "border-left-color: {color};"
        "border-right-color: {color};"
        "border-bottom-color: {color};"
        .format(width=width, color=color)
    )


def set_border_color_and_image(button, image, color, width=5):
    button.setStyleSheet(
        "border-image: url('{image}');"
        "border: {width}px solid;"
        "border-top-color: {color};"
        "border-left-color: {color};"
        "border-right-color: {color};"
        "border-bottom-color: {color};"
        .format(image=image, width=width, color=color)
    )
