import customtkinter as ctk
from tkinter import ttk, messagebox
from pymongo import MongoClient
from datetime import datetime

# ---------------------------------------------------------------------------
# CHECK INSTALLATIONS
# ---------------------------------------------------------------------------
try:
    import customtkinter
except:
    print("Run: pip install customtkinter")
    exit()

try:
    from pymongo import MongoClient
except:
    print("Run: pip install pymongo")
    exit()

# ---------------------------------------------------------------------------
# THEME SETUP - MODERN DARK/BLUE THEME
# ---------------------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Custom colors
COLORS = {
    "bg": "#1a1a2e",
    "card": "#16213e",
    "accent": "#0f3460",
    "accent_light": "#533483",
    "success": "#00b894",
    "danger": "#e17055",
    "warning": "#fdcb6e",
    "text": "#dfe6e9",
    "subtext": "#b2bec3"
}

# ---------------------------------------------------------------------------
# CONNECT TO DATABASE
# ---------------------------------------------------------------------------
db_ok = False
try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    client.server_info()
    db = client["ElectronicsStore"]
    products = db["inventory"]
    db_ok = True
    print("✅ Connected to MongoDB!")
except:
    print("❌ MongoDB not running!")

# ---------------------------------------------------------------------------
# CREATE MAIN WINDOW
# ---------------------------------------------------------------------------
app = ctk.CTk()
app.title("🛒 Electronics Store Inventory")
app.geometry("1300x750")
app.configure(fg_color=COLORS["bg"])

# =========================================================================
# ALL FUNCTIONS DEFINED FIRST
# =========================================================================

def clear_form():
    """Clear all input boxes"""
    id_entry.delete(0, "end")
    name_entry.delete(0, "end")
    brand_entry.delete(0, "end")
    category_entry.delete(0, "end")
    price_entry.delete(0, "end")
    quantity_entry.delete(0, "end")
    status_combo.set("In Stock")
    warranty_combo.set("1 Year")
    desc_entry.delete("1.0", "end")

def get_form_data():
    """Get data from form"""
    return {
        "product_id": id_entry.get(),
        "product_name": name_entry.get(),
        "brand": brand_entry.get(),
        "category": category_entry.get(),
        "price": price_entry.get(),
        "quantity": quantity_entry.get(),
        "status": status_combo.get(),
        "warranty": warranty_combo.get(),
        "description": desc_entry.get("1.0", "end-1c")
    }

def show_products():
    """Show all products in table"""
    for row in table.get_children():
        table.delete(row)
    
    if not db_ok:
        return
    
    count = 0
    for product in products.find({}, {"_id": 0}):
        table.insert("", "end", values=[
            product.get("product_id", ""),
            product.get("product_name", ""),
            product.get("brand", ""),
            product.get("category", ""),
            product.get("price", ""),
            product.get("quantity", ""),
            product.get("status", ""),
            product.get("warranty", "")
        ])
        count += 1
    
    total_label.configure(text=f"📊 Total Products: {count}")

def add_product():
    """Add new product"""
    if not db_ok:
        messagebox.showerror("Error", "Database not connected!")
        return
    
    data = get_form_data()
    
    if not data["product_id"] or not data["product_name"]:
        messagebox.showerror("Error", "Product ID and Name are required!")
        return
    
    if products.find_one({"product_id": data["product_id"]}):
        messagebox.showerror("Error", "Product ID already exists!")
        return
    
    products.insert_one(data)
    show_products()
    clear_form()
    messagebox.showinfo("Success", f"✅ Product '{data['product_name']}' added!")

def update_product():
    """Update existing product"""
    if not db_ok:
        messagebox.showerror("Error", "Database not connected!")
        return
    
    data = get_form_data()
    
    if not data["product_id"]:
        messagebox.showerror("Error", "Enter Product ID to update!")
        return
    
    if not products.find_one({"product_id": data["product_id"]}):
        messagebox.showerror("Error", "Product ID not found!")
        return
    
    products.update_one({"product_id": data["product_id"]}, {"$set": data})
    show_products()
    messagebox.showinfo("Success", f"✅ Product '{data['product_name']}' updated!")

def delete_product():
    """Delete product"""
    if not db_ok:
        messagebox.showerror("Error", "Database not connected!")
        return
    
    product_id = id_entry.get()
    
    if not product_id:
        messagebox.showerror("Error", "Enter Product ID to delete!")
        return
    
    product = products.find_one({"product_id": product_id})
    if not product:
        messagebox.showerror("Error", "Product not found!")
        return
    
    if messagebox.askyesno("Confirm", f"Delete '{product.get('product_name', product_id)}'?"):
        products.delete_one({"product_id": product_id})
        show_products()
        clear_form()
        messagebox.showinfo("Success", "✅ Product deleted!")

def select_product(event):
    """When click on a table row, fill the form"""
    selected = table.focus()
    if not selected:
        return
    
    values = table.item(selected)["values"]
    if not values:
        return
    
    clear_form()
    id_entry.insert(0, values[0])
    name_entry.insert(0, values[1])
    brand_entry.insert(0, values[2])
    category_entry.insert(0, values[3])
    price_entry.insert(0, values[4])
    quantity_entry.insert(0, values[5])
    status_combo.set(values[6])
    warranty_combo.set(values[7])

def search_products(query):
    """Search for products"""
    for row in search_table.get_children():
        search_table.delete(row)
    
    if not query.strip():
        search_total.configure(text="Results: 0")
        return
    
    count = 0
    for product in products.find({
        "$or": [
            {"product_id": {"$regex": query, "$options": "i"}},
            {"product_name": {"$regex": query, "$options": "i"}}
        ]
    }, {"_id": 0}):
        search_table.insert("", "end", values=[
            product.get("product_id", ""),
            product.get("product_name", ""),
            product.get("brand", ""),
            product.get("price", ""),
            product.get("quantity", ""),
            product.get("status", "")
        ])
        count += 1
    
    search_total.configure(text=f"Results: {count}")

def create_field(parent, label_text, placeholder="", is_dropdown=False, values=None):
    """Create a form field with label"""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", padx=15, pady=5)
    
    ctk.CTkLabel(frame, text=label_text, font=("Segoe UI", 12, "bold"), 
                 text_color=COLORS["text"]).pack(anchor="w")
    
    if is_dropdown:
        widget = ctk.CTkComboBox(frame, values=values, height=35, 
                                 fg_color=COLORS["bg"], border_color=COLORS["accent_light"])
    else:
        widget = ctk.CTkEntry(frame, placeholder_text=placeholder, height=35,
                              fg_color=COLORS["bg"], border_color=COLORS["accent_light"])
    widget.pack(fill="x", pady=(3, 0))
    return widget

def create_btn(parent, text, command, color, hover_color):
    """Create a styled button"""
    return ctk.CTkButton(parent, text=text, command=command, 
                         height=40, corner_radius=10, font=("Segoe UI", 12, "bold"),
                         fg_color=color, hover_color=hover_color)

# =========================================================================
# HEADER SECTION
# =========================================================================

header = ctk.CTkFrame(app, height=80, fg_color=COLORS["accent"], corner_radius=0)
header.pack(fill="x", pady=(0, 10))

header_left = ctk.CTkFrame(header, fg_color="transparent")
header_left.pack(side="left", padx=30, pady=15)

ctk.CTkLabel(header_left, text="🛒 Electronics Store", 
             font=("Segoe UI", 28, "bold"), text_color="white").pack(anchor="w")
ctk.CTkLabel(header_left, text="Inventory Management System", 
             font=("Segoe UI", 12), text_color=COLORS["subtext"]).pack(anchor="w")

header_right = ctk.CTkFrame(header, fg_color="transparent")
header_right.pack(side="right", padx=30)

status_text = "🟢 Online" if db_ok else "🔴 Offline"
status_color = COLORS["success"] if db_ok else COLORS["danger"]
ctk.CTkLabel(header_right, text=status_text, 
             font=("Segoe UI", 14, "bold"), text_color=status_color).pack()

# =========================================================================
# MAIN CONTENT - TABBED LAYOUT
# =========================================================================

tab_view = ctk.CTkTabview(app, fg_color=COLORS["card"], 
                           segmented_button_selected_color=COLORS["accent_light"],
                           segmented_button_unselected_color=COLORS["accent"])
tab_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))

# Tab 1: Manage Products
tab1 = tab_view.add("📦 Manage Products")
tab_view.set("📦 Manage Products")

# Tab 2: Search
tab2 = tab_view.add("🔍 Search")

# =========================================================================
# TAB 1: MANAGE PRODUCTS
# =========================================================================

main_frame = ctk.CTkFrame(tab1, fg_color="transparent")
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Left Column - Form
left_col = ctk.CTkScrollableFrame(main_frame, width=350, fg_color=COLORS["card"], 
                                   corner_radius=15)
left_col.pack(side="left", fill="y", padx=(0, 10))

ctk.CTkLabel(left_col, text="✏️ Product Details", 
             font=("Segoe UI", 18, "bold"), text_color="white").pack(pady=(15, 5))
ctk.CTkLabel(left_col, text="Fill in the information below", 
             font=("Segoe UI", 11), text_color=COLORS["subtext"]).pack(pady=(0, 15))

# Create all fields
id_entry = create_field(left_col, "📌 Product ID *", "e.g., PROD001")
name_entry = create_field(left_col, "📝 Product Name *", "e.g., iPhone 15 Pro")
brand_entry = create_field(left_col, "🏷️ Brand", "e.g., Apple")
category_entry = create_field(left_col, "📂 Category", "e.g., Smartphones")
price_entry = create_field(left_col, "💰 Price ($)", "e.g., 999")
quantity_entry = create_field(left_col, "📦 Quantity", "e.g., 15")

status_combo = create_field(left_col, "📊 Status", is_dropdown=True, 
                            values=["In Stock", "Low Stock", "Out of Stock"])
warranty_combo = create_field(left_col, "🛡️ Warranty", is_dropdown=True,
                              values=["6 Months", "1 Year", "2 Years", "3 Years", "No Warranty"])

# Description
desc_frame = ctk.CTkFrame(left_col, fg_color="transparent")
desc_frame.pack(fill="x", padx=15, pady=5)

ctk.CTkLabel(desc_frame, text="📝 Description", font=("Segoe UI", 12, "bold"), 
             text_color=COLORS["text"]).pack(anchor="w")
desc_entry = ctk.CTkTextbox(desc_frame, height=80, fg_color=COLORS["bg"], 
                             border_color=COLORS["accent_light"], border_width=1)
desc_entry.pack(fill="x", pady=(3, 0))

# Action Buttons
btn_frame = ctk.CTkFrame(left_col, fg_color="transparent")
btn_frame.pack(fill="x", padx=15, pady=20)

btn_row1 = ctk.CTkFrame(btn_frame, fg_color="transparent")
btn_row1.pack(fill="x", pady=3)
create_btn(btn_row1, "➕ Add Product", add_product, COLORS["success"], "#00a381").pack(side="left", fill="x", expand=True, padx=2)
create_btn(btn_row1, "✎ Update Product", update_product, "#0984e3", "#0873c7").pack(side="left", fill="x", expand=True, padx=2)

btn_row2 = ctk.CTkFrame(btn_frame, fg_color="transparent")
btn_row2.pack(fill="x", pady=3)
create_btn(btn_row2, "🗑 Delete Product", delete_product, COLORS["danger"], "#d63031").pack(side="left", fill="x", expand=True, padx=2)
create_btn(btn_row2, "✕ Clear Form", clear_form, COLORS["warning"], "#fdcb6e").pack(side="left", fill="x", expand=True, padx=2)

# Right Column - Table
right_col = ctk.CTkFrame(main_frame, fg_color=COLORS["card"], corner_radius=15)
right_col.pack(side="right", fill="both", expand=True)

ctk.CTkLabel(right_col, text="📋 Product List", 
             font=("Segoe UI", 18, "bold"), text_color="white").pack(anchor="w", padx=20, pady=(15, 5))

# Stats bar
stats_frame = ctk.CTkFrame(right_col, fg_color="transparent")
stats_frame.pack(fill="x", padx=20, pady=(0, 10))

total_label = ctk.CTkLabel(stats_frame, text="📊 Total Products: 0", 
                           font=("Segoe UI", 12), text_color=COLORS["subtext"])
total_label.pack(side="left")

# Table
table_frame = ctk.CTkFrame(right_col, fg_color="transparent")
table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background=COLORS["bg"], foreground="white", 
                fieldbackground=COLORS["bg"], rowheight=30, font=("Segoe UI", 10))
style.configure("Treeview.Heading", background=COLORS["accent_light"], 
                foreground="white", font=("Segoe UI", 11, "bold"))
style.map("Treeview", background=[("selected", COLORS["accent_light"])])

scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
table = ttk.Treeview(table_frame, columns=("ID", "Name", "Brand", "Category", "Price", "Qty", "Status", "Warranty"), 
                     show="headings", height=18, yscrollcommand=scrollbar.set)
scrollbar.config(command=table.yview)

columns_config = {
    "ID": 80, "Name": 150, "Brand": 100, "Category": 100, 
    "Price": 80, "Qty": 60, "Status": 100, "Warranty": 100
}
for col, width in columns_config.items():
    table.heading(col, text=col)
    table.column(col, width=width, anchor="w")

table.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")
table.bind("<<TreeviewSelect>>", select_product)

# =========================================================================
# TAB 2: SEARCH
# =========================================================================

search_frame = ctk.CTkFrame(tab2, fg_color="transparent")
search_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Search bar
search_bar = ctk.CTkFrame(search_frame, fg_color=COLORS["card"], corner_radius=15)
search_bar.pack(fill="x", pady=(0, 20))

search_input = ctk.CTkEntry(search_bar, placeholder_text="🔍 Search by Product ID or Name...", 
                             height=45, font=("Segoe UI", 14), fg_color=COLORS["bg"])
search_input.pack(side="left", fill="x", expand=True, padx=20, pady=15)

search_btn = ctk.CTkButton(search_bar, text="Search", 
                           command=lambda: search_products(search_input.get()),
                           fg_color=COLORS["accent_light"], height=45, width=100)
search_btn.pack(side="right", padx=20, pady=15)

# Search results
search_results_frame = ctk.CTkFrame(search_frame, fg_color=COLORS["card"], corner_radius=15)
search_results_frame.pack(fill="both", expand=True)

search_total = ctk.CTkLabel(search_results_frame, text="Results: 0", 
                            font=("Segoe UI", 12), text_color=COLORS["subtext"])
search_total.pack(anchor="w", padx=20, pady=10)

# Table for search results
search_table_frame = ctk.CTkFrame(search_results_frame, fg_color="transparent")
search_table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

search_scroll = ttk.Scrollbar(search_table_frame, orient="vertical")
search_table = ttk.Treeview(search_table_frame, columns=("ID", "Name", "Brand", "Price", "Qty", "Status"), 
                            show="headings", height=15, yscrollcommand=search_scroll.set)
search_scroll.config(command=search_table.yview)

for col in ["ID", "Name", "Brand", "Price", "Qty", "Status"]:
    search_table.heading(col, text=col)
    search_table.column(col, width=100)

search_table.pack(side="left", fill="both", expand=True)
search_scroll.pack(side="right", fill="y")

# =========================================================================
# START APPLICATION
# =========================================================================

show_products()

# Show warning if MongoDB not connected
if not db_ok:
    messagebox.showwarning("Database Warning", 
                          "MongoDB is not running!\nPlease start MongoDB to use all features.")

app.mainloop()