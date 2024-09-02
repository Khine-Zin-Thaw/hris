// ddsmoothmenu.js

// Define the SmoothMenu class
class SmoothMenu {
    constructor(menuId) {
        this.menu = document.getElementById(menuId);
        this.initMenu();
    }

    // Initialize the menu
    initMenu() {
        if (!this.menu) return;
        
        // Get all menu items
        this.menuItems = this.menu.querySelectorAll('li');

        // Add event listeners to menu items
        this.menuItems.forEach(item => {
            item.addEventListener('mouseover', () => this.showSubMenu(item));
            item.addEventListener('mouseout', () => this.hideSubMenu(item));
        });
    }

    // Show submenu with a smooth transition
    showSubMenu(menuItem) {
        const subMenu = menuItem.querySelector('ul');
        if (subMenu) {
            subMenu.style.display = 'block';
            subMenu.style.opacity = 0;
            let opacity = 0;
            const interval = setInterval(() => {
                if (opacity >= 1) {
                    clearInterval(interval);
                } else {
                    opacity += 0.1;
                    subMenu.style.opacity = opacity;
                }
            }, 50);
        }
    }

    // Hide submenu with a smooth transition
    hideSubMenu(menuItem) {
        const subMenu = menuItem.querySelector('ul');
        if (subMenu) {
            subMenu.style.opacity = 1;
            let opacity = 1;
            const interval = setInterval(() => {
                if (opacity <= 0) {
                    clearInterval(interval);
                    subMenu.style.display = 'none';
                } else {
                    opacity -= 0.1;
                    subMenu.style.opacity = opacity;
                }
            }, 50);
        }
    }
}

// Initialize the menu when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SmoothMenu('menu'); // Pass the ID of your menu
});
