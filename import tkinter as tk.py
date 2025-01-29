import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox, Toplevel
import json
from tk import Image, ImageDraw

class GenealogyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arbre Généalogique")
        
        # Canvas pour l'affichage graphique
        self.canvas = tk.Canvas(root, bg="green", width=1200, height=800, scrollregion=(0, 0, 2000, 2000))
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Variables pour gérer le zoom
        self.scale_factor = 1.0

        # Barre de défilement
        self.scroll_x = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.scroll_y = tk.Scrollbar(root, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scroll_x.pack(fill=tk.X, side=tk.BOTTOM)
        self.scroll_y.pack(fill=tk.Y, side=tk.RIGHT)
        self.canvas.configure(xscrollcommand=self.scroll_x.set, yscrollcommand=self.scroll_y.set)
        
        # Boutons
        self.control_frame = tk.Frame(root, bg="green")
        self.control_frame.pack(fill=tk.X)
        button_style = {"bg": "green", "fg": "white", "font": ("Arial", 10), "activebackground": "darkgreen"}
        tk.Button(self.control_frame, text="Nouvelle Personne", command=self.add_person, **button_style).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.control_frame, text="Sauvegarder", command=self.save_tree, **button_style).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.control_frame, text="Charger", command=self.load_tree, **button_style).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.control_frame, text="Zoom Avant", command=lambda: self.zoom(1.1), **button_style).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.control_frame, text="Zoom Arrière", command=lambda: self.zoom(0.9), **button_style).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.control_frame, text="Exporter en PNG", command=self.export_image, **button_style).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Variables pour stocker les données
        self.tree_data = {}  # Stocke l'arbre en mémoire
        self.rectangles = {}  # Associe les identifiants graphiques aux données
        self.current_id = 1  # Identifiant unique pour chaque personne

        # Lier des événements pour le zoom
        self.canvas.bind("<MouseWheel>", self.zoom_mouse)  # Molette pour zoomer
        self.canvas.bind("<Double-1>", self.open_notes)    # Double clic pour ouvrir les notes

    def add_person(self):
        """Ajoute une personne à l'arbre avec un formulaire"""
        data = {}
        data['nom'] = simpledialog.askstring("Entrer le nom", "Nom:")
        data['prenom'] = simpledialog.askstring("Entrer le prénom", "Prénom:")
        data['naissance'] = simpledialog.askstring("Entrer la date de naissance", "Date de naissance:")
        data['deces'] = simpledialog.askstring("Entrer la date de décès", "Date de décès (laisser vide si vivant):")
        data['mariage'] = simpledialog.askstring("Entrer la date de mariage", "Date de mariage (optionnel):")
        data['notes'] = simpledialog.askstring("Ajouter des notes", "Notes personnelles (optionnel):")
        
        if not data['nom'] or not data['prenom']:
            messagebox.showerror("Erreur", "Le nom et le prénom sont obligatoires.")
            return
        
        parent_id = simpledialog.askinteger("Relier à un parent", "Entrer l'ID du parent (laisser vide pour nouvelle racine):", initialvalue=0)
        parent_id = parent_id if parent_id in self.tree_data else None
        
        self.create_case(data, parent_id)

    def create_case(self, data, parent_id=None):
        x, y = 500, 50
        
        if parent_id:
            parent_rect = self.rectangles[parent_id]
            parent_coords = self.canvas.coords(parent_rect)
            x = (parent_coords[0] + parent_coords[2]) / 2
            y = parent_coords[3] + 100
            
        width, height = 200, 85
        rect = self.canvas.create_rectangle(
            x - width // 2, y, x + width // 2, y + height, fill="black", outline="white"
        )
        text = f"{data['nom']} {data['prenom']}\nNaissance: {data['naissance']}\nDécès: {data['deces'] or 'N/A'}\nMariage: {data['mariage'] or 'N/A'}"
        self.canvas.create_text(x, y + height // 2, text=text, font=("Arial", 10), fill="white")
        
        if parent_id:
            parent_coords = self.canvas.coords(self.rectangles[parent_id])
            self.canvas.create_line(
                (parent_coords[0] + parent_coords[2]) / 2, parent_coords[3],
                x, y, fill="white"
            )
        
        person_id = self.current_id
        self.tree_data[person_id] = {
            "data": data,
            "parent_id": parent_id,
            "coords": (x, y)
        }
        self.rectangles[person_id] = rect
        self.current_id += 1

    def open_notes(self, event):
        """Ouvre une nouvelle fenêtre pour afficher ou éditer les notes"""
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        for person_id, rect_id in self.rectangles.items():
            coords = self.canvas.coords(rect_id)
            if coords[0] <= x <= coords[2] and coords[1] <= y <= coords[3]:
                notes = self.tree_data[person_id]['data'].get('notes', 'Pas de notes.')
                
                # Fenêtre de notes
                note_window = Toplevel(self.root)
                note_window.title(f"Notes pour {self.tree_data[person_id]['data']['nom']} {self.tree_data[person_id]['data']['prenom']}")
                text_box = tk.Text(note_window, wrap=tk.WORD, width=50, height=20, bg="black", fg="white", insertbackground="white")
                text_box.pack(fill=tk.BOTH, expand=True)
                text_box.insert("1.0", notes)
                
                def save_notes():
                    self.tree_data[person_id]['data']['notes'] = text_box.get("1.0", tk.END).strip()
                    note_window.destroy()
                
                tk.Button(note_window, text="Sauvegarder", command=save_notes, **button_style).pack(pady=5)
                return

    def zoom_mouse(self, event):
        """Zoom avec la molette de la souris centré sur la position du curseur"""
        scale_factor = 1.1 if event.delta > 0 else 0.9
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.scale("all", x, y, scale_factor, scale_factor)
        self.scale_factor *= scale_factor
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def zoom(self, factor):
        """Zoom avant ou arrière via bouton"""
        self.canvas.scale("all", 0, 0, factor, factor)
        self.scale_factor *= factor
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def save_tree(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path:
            return
        
        with open(file_path, "w") as file:
            json.dump(self.tree_data, file)
        
        messagebox.showinfo("Succès", "Arbre généalogique sauvegardé avec succès !")

    def load_tree(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path:
            return
        
        with open(file_path, "r") as file:
            self.tree_data = json.load(file)
        
        self.canvas.delete("all")
        self.rectangles = {}
        self.current_id = 1
        
        for person_id, person in self.tree_data.items():
            self.create_case(person['data'], person['parent_id'])
        
        messagebox.showinfo("Succès", "Arbre généalogique chargé avec succès !")

    def export_image(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if not file_path:
            return
        
        # Créer une image avec PIL
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        image = Image.new("RGB", (width, height), "green")
        draw = ImageDraw.Draw(image)
        
        for item in self.canvas.find_all():
            coords = self.canvas.coords(item)
            if len(coords) == 4:  # Rectangle
                draw.rectangle(coords, outline="white", fill="black")
            elif len(coords) == 2:  # Texte ou ligne
                text = self.canvas.itemcget(item, "text")
                if text:
                    draw.text(coords, text, fill="white")
        
        image.save(file_path)
        messagebox.showinfo("Succès", "Arbre exporté avec succès en image !")

# Lancer l'application
if __name__ == "__main__":
    root = tk.Tk()
    app = GenealogyApp(root)
    root.mainloop()
