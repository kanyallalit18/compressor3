from tkinterdnd2 import DND_FILES, TkinterDnD
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import heapq
import os
import pickle

# ---------------- Huffman + RLE Logic ---------------- #

class HuffmanNode:
    def __init__(self, byte, freq):
        self.byte = byte
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(data):
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1

    heap = [HuffmanNode(b, f) for b, f in freq.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        l = heapq.heappop(heap)
        r = heapq.heappop(heap)
        merged = HuffmanNode(None, l.freq + r.freq)
        merged.left = l
        merged.right = r
        heapq.heappush(heap, merged)

    return heap[0]

def build_codes(node, current_code=b"", codes=None):
    if codes is None:
        codes = {}
    if node:
        if node.byte is not None:
            codes[node.byte] = current_code
        build_codes(node.left, current_code + b"0", codes)
        build_codes(node.right, current_code + b"1", codes)
    return codes

def encode_data(data, codes):
    bitstring = ""
    for byte in data:
        bitstring += codes[byte].decode()

    padding = 8 - len(bitstring) % 8
    bitstring += '0' * padding
    padded_info = "{0:08b}".format(padding)
    bitstring = padded_info + bitstring

    b = bytearray()
    for i in range(0, len(bitstring), 8):
        byte = bitstring[i:i+8]
        b.append(int(byte, 2))
    return b

def decode_data(encoded_bytes, codes):
    bitstring = ""
    for byte in encoded_bytes:
        bitstring += f"{byte:08b}"

    if len(bitstring) < 8:
        raise ValueError("The bitstring is too short to contain padding information.")

    padding = int(bitstring[:8], 2)
    bitstring = bitstring[8:-padding] if padding > 0 else bitstring[8:]

    reverse_codes = {v.decode(): k for k, v in codes.items()}
    current_code = ""
    decoded = bytearray()

    for bit in bitstring:
        current_code += bit
        if current_code in reverse_codes:
            decoded.append(reverse_codes[current_code])
            current_code = ""

    return decoded

def huffman_compress(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()

    root = build_huffman_tree(data)
    codes = build_codes(root)
    encoded = encode_data(data, codes)

    output_path = filedialog.asksaveasfilename(defaultextension=".huff", filetypes=[("Huffman files", "*.huff")])
    if output_path:
        with open(output_path, 'wb') as f:
            original_ext = os.path.splitext(file_path)[1]
            pickle.dump((codes, original_ext), f)
            f.write(encoded)
        progress['value'] = 100
        messagebox.showinfo("Success", f"Compressed using Huffman:\n{output_path}")
    progress['value'] = 0

def huffman_decompress(file_path):
    try:
        with open(file_path, 'rb') as f:
            codes, original_ext = pickle.load(f)
            encoded = f.read()
        if not encoded:
            messagebox.showerror("Error", "The compressed file is empty or corrupted.")
            return
        decoded = decode_data(encoded, codes)

        output_path = filedialog.asksaveasfilename(defaultextension=original_ext, filetypes=[("All files", "*.*")])
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(decoded)
            progress['value'] = 100
            messagebox.showinfo("Success", f"Decompressed using Huffman:\n{output_path}")
        progress['value'] = 0

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        progress['value'] = 0

def rle_compress(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()

    compressed = bytearray()
    total = len(data)
    i = 0
    while i < len(data):
        count = 1
        while i + 1 < len(data) and data[i] == data[i + 1] and count < 255:
            count += 1
            i += 1
        compressed.extend([data[i], count])
        i += 1
        update_progress(i, total)

    output_path = filedialog.asksaveasfilename(defaultextension=".rle", filetypes=[("RLE files", "*.rle")])
    if output_path:
        with open(output_path, 'wb') as f:
            original_ext = os.path.splitext(file_path)[1]
            pickle.dump((original_ext,), f)
            f.write(compressed)
        messagebox.showinfo("Success", f"Compressed using RLE:\n{output_path}")
    progress['value'] = 0

def rle_decompress(file_path):
    with open(file_path, 'rb') as f:
        original_ext_tuple = pickle.load(f)
        original_ext = original_ext_tuple[0]
        compressed = f.read()

    decompressed = bytearray()
    for i in range(0, len(compressed), 2):
        byte = compressed[i]
        count = compressed[i + 1]
        decompressed.extend([byte] * count)
        update_progress(i, len(compressed))

    output_path = filedialog.asksaveasfilename(defaultextension=original_ext)
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(decompressed)
        messagebox.showinfo("Success", f"Decompressed using RLE:\n{output_path}")
    progress['value'] = 0

def update_progress(current, total):
    if total > 0:
        percent = (current / total) * 100
        progress['value'] = percent
        root.update_idletasks()

# ---------------- GUI ---------------- #

def choose_file():
    path = filedialog.askopenfilename()
    if path:
        selected_file.set(path)
        file_entry.config(state='normal')
        file_entry.delete(0, tk.END)
        file_entry.insert(0, path)
        file_entry.config(state='disabled')

def compress():
    file_path = selected_file.get()
    if not file_path or not os.path.isfile(file_path):
        messagebox.showerror("Error", "Choose a valid file first.")
        return
    if "Huffman" in selected_option.get():
        huffman_compress(file_path)
    else:
        rle_compress(file_path)

def decompress():
    file_path = filedialog.askopenfilename()
    if not file_path:
        return
    if "Huffman" in selected_option.get():
        huffman_decompress(file_path)
    else:
        rle_decompress(file_path)

def show_about():
    popup = tk.Toplevel(root)
    popup.title("About")
    popup.configure(bg="#2a2a2a")
    popup.geometry("400x200")
    popup.resizable(False, False)
    tk.Label(
        popup,
        text="This is a modern file compression tool.\n\n"
             "- Huffman (Lossless)\n- RLE (Basic)\n- Drag and Drop\n- Dark Mode UI",
        justify="left", bg="#2a2a2a", fg="white", font=("Arial", 11), padx=10, pady=10
    ).pack()

def drop(event):
    path = event.data.strip("{}")
    selected_file.set(path)
    file_entry.config(state='normal')
    file_entry.delete(0, tk.END)
    file_entry.insert(0, path)
    file_entry.config(state='disabled')

# TkinterDnD root
root = TkinterDnD.Tk()
root.title("Modern File Compression Tool")
root.geometry("620x500")
root.resizable(False, False)
root.configure(bg="#1e1e1e")
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', drop)

# Menu bar
menu_bar = tk.Menu(root)
menu_bar.add_command(label="About", command=show_about)
root.config(menu=menu_bar)

tk.Label(root, text="File Compression Tool", font=("Segoe UI", 20), bg="#1e1e1e", fg="white").pack(pady=15)

# Compression type
tk.Label(root, text="Choose compression type:", font=("Segoe UI", 13), bg="#1e1e1e", fg="white").pack(pady=5)
optionarr = ["Huffman (Lossless)", "RLE (Basic)"]
selected_option = tk.StringVar(value=optionarr[0])
dropdown = ttk.Combobox(root, textvariable=selected_option, values=optionarr, state="readonly", font=("Segoe UI", 12))
dropdown.pack(pady=5)

# File selection
file_frame = tk.Frame(root, bg="#1e1e1e")
file_frame.pack(pady=10)
selected_file = tk.StringVar()
choose_btn = tk.Button(file_frame, text="Choose File", command=choose_file, bg="#333", fg="white", width=12)
choose_btn.pack(side=tk.LEFT)
file_entry = tk.Entry(file_frame, textvariable=selected_file, width=40, state="disabled", font=("Segoe UI", 10), bg="#333", fg="white")
file_entry.pack(side=tk.LEFT, padx=10)

# Buttons
tk.Button(root, text="Compress", command=compress, width=15, height=2, bg="#444", fg="white").pack(pady=5)
tk.Button(root, text="Decompress", command=decompress, width=15, height=2, bg="#444", fg="white").pack(pady=5)

# Progress bar
progress_frame = tk.Frame(root, bg="#1e1e1e")
progress_frame.pack(pady=20)
tk.Label(progress_frame, text="Progress", font=("Segoe UI", 12), bg="#1e1e1e", fg="white").pack(side=tk.LEFT, padx=10)
progress = ttk.Progressbar(progress_frame, orient="horizontal", length=300, mode="determinate")
progress.pack(side=tk.LEFT)

root.mainloop()
