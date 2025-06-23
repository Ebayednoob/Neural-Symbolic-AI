import os
import json
import networkx as nx
import matplotlib.pyplot as plt
import threading
import re

# --- GUI ---
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog, filedialog
from PIL import Image, ImageTk # Pillow library is required for image handling

# --- LLM Processing ---
import requests

class LLMProcessor:
    """Handles interaction with the Gemini LLM for data parsing and generation."""
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"

    def create_parsing_prompt(self):
        """Creates the detailed instruction prompt for parsing raw data."""
        return """
You are an expert data parsing assistant. Your task is to read raw text containing behavioral theory data and convert it into a structured JSON object. The JSON object must have three keys: "constructs", "triples", and "annotations".

1.  **Parse "Theory triples"**:
    * This section starts with the line "Theory triples".
    * Each line represents a relationship: "Subject Predicate Object".
    * Convert each line into a JSON object `{"subject": "...", "predicate": "...", "object": "..."}`.
    * For complex relationships like "Subject influences the 'ObjectA' to 'ObjectB' Predicate relationship", the object is the entire quoted phrase. Example: `{"subject": "Situational Forces", "predicate": "influences", "object": "the 'Performance of goal-directed behaviours' to 'Goal attainment / failure' Influences relationship"}`.
    * The output should be a JSON list under the key "triples".

2.  **Parse "Theory constructs and annotations"**:
    * This section starts with "Theory constructs and annotations".
    * From this section, you will populate TWO JSON lists: "constructs" and "annotations".
    * **"constructs" list**: Create a list of all unique construct names found in this section. Each item should be a JSON object `{"name": "Construct Name", "description": ""}`. The description will be empty.
    * **"annotations" list**: Each line in the raw text represents one or more annotations for a construct. A line looks like: `ConstructName [ ID (Value) SourceNumbers , ID2 (Value2) SourceNumbers2 ]`.
    * For each annotation block `[ ... ]`, create a separate JSON object.
    * Each annotation object must have the keys: "construct", "relation", "value", "source".
    * `"construct"`: The name of the construct on that line.
    * `"relation"`: The identifier string (e.g., "BCIO:050564").
    * `"value"`: The text inside the parentheses (e.g., "Affective attitude acquired through association").
    * `"source"`: All the numbers following the value, joined into a single string (e.g., "1 82 69 22 5"). If there is only one number, it is the source.

Example: `Desire [ MF:0000045 (Wanting) 1 , BCIO:006075 (Subjective need) 1 82 69 22 5 ]` should produce TWO annotation objects:
- `{"construct": "Desire", "relation": "MF:0000045", "value": "Wanting", "source": "1"}`
- `{"construct": "Desire", "relation": "BCIO:006075", "value": "Subjective need", "source": "1 82 69 22 5"}`

Output ONLY the final, validated JSON object and nothing else.
"""

    def create_description_prompt(self, theory_name, constructs, triples):
        """Creates a prompt for the LLM to generate a theory description."""
        construct_list = "\n".join([f"- {c['name']}" for c in constructs])
        triple_list = "\n".join([f"- {t['subject']} {t['predicate']} {t['object']}" for t in triples])
        
        return f"""
You are a behavioral science expert. Based on the provided components of a theory, write a concise, academic paragraph summarizing it. The summary should explain the core idea of the theory by integrating its constructs and their relationships.

**Theory Name:** {theory_name}
**Core Constructs:**
{construct_list}
**Relationships (Triples):**
{triple_list}

**Generated Summary:**
"""

    def create_chat_prompt(self):
        """Creates the system prompt for the conversational chat agent."""
        return """
You are a conversational AI assistant embedded in a data entry tool for behavioral theories.
Your capabilities are:
1.  **Answering Questions**: You can answer questions about any of the theories provided in the context.
2.  **Modifying Data**: You can modify the data for the **currently selected theory ONLY**. The current theory is identified by its ID.

**Input Format:**
The user's prompt will be preceded by the full JSON data of all theories and the ID of the currently selected one.

**Output Format:**
You MUST respond with a single JSON object. Your response format depends on the user's request:

A) **For simple conversation or questions** (e.g., "Hello", "What is Theory of Planned Behavior?", "Compare theory 1 and 2"):
   Respond with a JSON object containing a single "response" key.
   Example:
   {
     "response": "Hello! I am ready to assist you with your behavioral theories. How can I help?"
   }

B) **For modification requests** (e.g., "change the name to 'New Name'", "add a construct for 'self-efficacy'", "remove the triple about desire", "update the description"):
   1. Perform the requested change on the JSON data of the **currently selected theory**.
   2. Respond with a JSON object containing a single "updated_theory_data" key.
   3. The value of this key MUST be the **complete, entire JSON object for the modified theory**, reflecting the changes. Do not just return the changed part.

**Example Modification Request:**
- User asks: "For the current theory, add a construct named 'Test Construct' with the description 'A test.'"
- Your response should be:
  {
    "updated_theory_data": {
      "id": 1,
      "name": "Theory 1",
      "description": "...",
      "picture_path": "...",
      "complete": false,
      "constructs": [
         ... existing constructs ...,
        {"name": "Test Construct", "description": "A test."}
      ],
      "triples": [...],
      "annotations": [...]
    }
  }

If a request is ambiguous, ask for clarification. Do not make assumptions. Always adhere to the JSON output format.
"""

    def make_api_call(self, prompt_text):
        """Generic method to make an API call to the LLM."""
        payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            result_json = response.json()
            content_text = result_json['candidates'][0]['content']['parts'][0]['text']
            return content_text
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Network Error", f"Failed to connect to the API: {e}")
            return None
        except (KeyError, IndexError) as e:
            messagebox.showerror("API Error", f"Could not parse the API's response: {e}\n\nResponse was:\n{result_json}")
            return None

    def parse_raw_text(self, raw_text):
        """Sends the raw text to the LLM and gets structured data back."""
        prompt = self.create_parsing_prompt() + "\n\nHere is the raw data to parse:\n\n" + raw_text
        content_text = self.make_api_call(prompt)
        if content_text:
            try:
                cleaned_json_text = content_text.strip().replace('```json', '').replace('```', '').strip()
                return json.loads(cleaned_json_text)
            except json.JSONDecodeError as e:
                messagebox.showerror("Parsing Error", f"Could not parse the LLM's JSON response: {e}\n\nResponse was:\n{content_text}")
                return None
        return None
        
    def generate_description(self, theory_name, constructs, triples):
        """Sends theory data to LLM to generate a description."""
        prompt = self.create_description_prompt(theory_name, constructs, triples)
        return self.make_api_call(prompt)

    def chat(self, user_message, all_theories_json, current_theory_id):
        """Handles a conversational chat turn."""
        prompt = (f"{self.create_chat_prompt()}\n\n"
                  f"--- Full Data Context ---\n{all_theories_json}\n\n"
                  f"--- Current Theory ID for Modification ---\n{current_theory_id}\n\n"
                  f"--- User Message ---\n{user_message}")
        content_text = self.make_api_call(prompt)
        if content_text:
            try:
                cleaned_json_text = content_text.strip().replace('```json', '').replace('```', '').strip()
                return json.loads(cleaned_json_text)
            except json.JSONDecodeError as e:
                messagebox.showerror("Chat Error", f"Could not parse the LLM's chat response: {e}\n\nResponse was:\n{content_text}")
                return None
        return None

class TheoryDataManager:
    def __init__(self, filepath="theory_data.json"):
        self.filepath = filepath
        self.theories = []
        self.graph = nx.DiGraph()
        self.load_data()

    def load_data(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.theories = json.load(f)
        else:
            self.theories = [{"id": i, "name": f"Theory {i}", "description": "", "picture_path": "", "complete": False, "constructs": [], "triples": [], "annotations": []} for i in range(1, 77)]
            self.save_data()

    def save_data(self):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.theories, f, indent=4)

    def get_theory(self, theory_id):
        return self.theories[theory_id - 1]

    def update_theory(self, theory_id, data):
        self.theories[theory_id - 1] = data
        self.save_data()

    def build_graph(self):
        self.graph = nx.DiGraph()
        all_constructs = {}
        for theory in self.theories:
            for construct in theory.get('constructs', []):
                all_constructs[construct['name']] = construct['description']
        
        for name, desc in all_constructs.items():
            self.graph.add_node(name, type='construct', description=desc)

        for theory in self.theories:
            if not theory.get('complete'): continue
            theory_name = theory['name']
            self.graph.add_node(theory_name, type='theory', description=theory.get('description', ''))
            
            for construct in theory.get('constructs', []): self.graph.add_edge(theory_name, construct['name'], label='has_construct')
            for triple in theory.get('triples', []):
                subj, pred, obj = triple['subject'], triple['predicate'], triple['object']
                if not self.graph.has_node(subj): self.graph.add_node(subj, type='construct')
                if not self.graph.has_node(obj): self.graph.add_node(obj, type='construct')
                self.graph.add_edge(subj, obj, label=pred)
            for annotation in theory.get('annotations', []):
                node_name = annotation['construct']
                if self.graph.has_node(node_name):
                    if 'annotations' not in self.graph.nodes[node_name]:
                        self.graph.nodes[node_name]['annotations'] = []
                    self.graph.nodes[node_name]['annotations'].append(f"{annotation['relation']}: {annotation['value']} (Source: {annotation['source']})")

    def visualize_graph(self):
        if self.graph.number_of_nodes() == 0:
            messagebox.showwarning("Graph Empty", "No completed theories to visualize.")
            return
        
        messagebox.showinfo("Visualize Graph", "The graph will be generated in a new window.")
        plt.figure(figsize=(40, 40))
        try:
            from networkx.drawing.nx_pydot import graphviz_layout
            pos = graphviz_layout(self.graph, prog='neato')
        except ImportError:
            pos = nx.spring_layout(self.graph, k=0.15, iterations=20)
        
        node_colors = ['red' if n[1]['type'] == 'theory' else 'skyblue' for n in self.graph.nodes(data=True)]
        nx.draw(self.graph, pos, with_labels=True, node_color=node_colors, node_size=2000, font_size=8, arrows=True)
        edge_labels = nx.get_edge_attributes(self.graph, 'label')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_size=7, font_color='green')
        
        plt.title("Behavioral Theory Relational Graph", size=40)
        if not os.path.exists("output"): os.makedirs("output")
        plt.savefig("output/behavioral_theory_relational_graph.png", bbox_inches='tight', dpi=300)
        plt.show()

class TheoryDataEntryGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Behavioral Theory Data Entry Tool")
        self.root.geometry("1400x900")
        self.data_manager = TheoryDataManager()
        self.current_theory_id = None
        self.current_image_path = ""
        
        self.main_pane = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.main_pane, width=300)
        self.main_pane.add(self.left_frame, weight=1)
        
        ttk.Button(self.left_frame, text="Show Incomplete Theories", command=self.show_incomplete_theories).pack(pady=(10,0), padx=10, fill=tk.X)

        self.tree = ttk.Treeview(self.left_frame, columns=('status',))
        self.tree.heading('#0', text='Theory')
        self.tree.heading('status', text='Status')
        self.tree.column('status', width=80, anchor='center')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind('<<TreeviewSelect>>', self.on_theory_select)
        self.populate_theory_list()

        self.right_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(self.right_frame, weight=3)
        
        self.setup_right_pane()
        self.set_entry_state('disabled')

    def setup_right_pane(self):
        top_controls_frame = ttk.Frame(self.right_frame)
        top_controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_controls_frame, text="Save Changes for This Theory", command=self.save_current_theory).pack(side=tk.LEFT)
        ttk.Button(top_controls_frame, text="Export to Cypher", command=self.export_theory_to_cypher).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_controls_frame, text="Build & Visualize Final Graph", command=self.build_and_visualize).pack(side=tk.RIGHT)
        
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.setup_general_tab()
        self.setup_constructs_tab()
        self.setup_triples_tab()
        self.setup_annotations_tab()
        self.setup_llm_entry_tab()
        self.setup_settings_tab()

    def setup_general_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='1. General')
        
        main_frame = ttk.Frame(tab)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        top_pane = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        top_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        text_frame = ttk.Frame(top_pane)
        top_pane.add(text_frame, weight=1)

        ttk.Label(text_frame, text="Theory Name:").pack(anchor='w', padx=5, pady=(5,0))
        self.theory_name_var = tk.StringVar()
        ttk.Entry(text_frame, textvariable=self.theory_name_var).pack(fill=tk.X, padx=5)

        ttk.Label(text_frame, text="Theory Description:").pack(anchor='w', padx=5, pady=(5,0))
        self.theory_desc_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=5)
        self.theory_desc_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0,5))
        
        ttk.Button(text_frame, text="Generate Description with LLM", command=self.generate_description_with_llm).pack(pady=5)
        
        image_frame = ttk.LabelFrame(top_pane, text="Theory Image")
        top_pane.add(image_frame, weight=1)
        
        self.image_label = ttk.Label(image_frame, text="No Image Selected")
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Button(image_frame, text="Select Image", command=self.select_image).pack(pady=5)
        
        chat_frame = ttk.LabelFrame(main_frame, text="Chat with LLM about this Theory")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.chat_history = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, state='disabled', font=("Arial", 10))
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        chat_input_frame = ttk.Frame(chat_frame)
        chat_input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.chat_entry = ttk.Entry(chat_input_frame, font=("Arial", 10))
        self.chat_entry.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.chat_entry.bind("<Return>", self.send_chat_message)
        
        self.send_button = ttk.Button(chat_input_frame, text="Send", command=self.send_chat_message)
        self.send_button.pack(side=tk.RIGHT, padx=5)
        
        self.theory_complete_var = tk.BooleanVar()
        ttk.Checkbutton(tab, text="Mark this theory as complete", variable=self.theory_complete_var).pack(pady=10, side=tk.BOTTOM)

    def setup_llm_entry_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='LLM Bulk Entry')
        llm_frame = ttk.LabelFrame(tab, text="Parse Raw Data with LLM")
        llm_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        controls = ttk.Frame(llm_frame)
        controls.pack(fill=tk.X, pady=5)
        ttk.Label(controls, text="Target Theory:").pack(side=tk.LEFT)
        self.llm_target_theory_var = tk.StringVar()
        theory_names = [t['name'] for t in self.data_manager.theories]
        self.llm_target_theory_combo = ttk.Combobox(controls, textvariable=self.llm_target_theory_var, values=theory_names, state='readonly')
        self.llm_target_theory_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Process Data with LLM", command=self.process_with_llm).pack(side=tk.RIGHT)
        self.llm_input_text = scrolledtext.ScrolledText(llm_frame, wrap=tk.WORD)
        self.llm_input_text.pack(fill=tk.BOTH, expand=True, pady=5)

    def setup_settings_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Settings')
        settings_frame = ttk.LabelFrame(tab, text="API Configuration")
        settings_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(settings_frame, text="Gemini API Key:").pack(side=tk.LEFT, padx=5)
        self.api_key_var = tk.StringVar()
        ttk.Entry(settings_frame, textvariable=self.api_key_var, width=60, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(settings_frame, text="Save Key", command=self.save_api_key).pack(side=tk.LEFT, padx=5)
        self.load_api_key()

    def setup_constructs_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='2. Constructs')
        controls = ttk.Frame(tab)
        controls.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(controls, text="Add Construct", command=self.add_construct).pack(side=tk.LEFT)
        ttk.Button(controls, text="Edit Selected", command=self.edit_construct).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Remove Selected", command=self.remove_construct).pack(side=tk.LEFT)
        self.constructs_tree = ttk.Treeview(tab, columns=('name', 'desc'), show='headings')
        self.constructs_tree.heading('name', text='Construct Name')
        self.constructs_tree.heading('desc', text='Description')
        self.constructs_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def setup_triples_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='3. Triples (Relationships)')
        controls = ttk.Frame(tab)
        controls.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(controls, text="Add Triple", command=self.add_triple).pack(side=tk.LEFT)
        ttk.Button(controls, text="Remove Selected", command=self.remove_triple).pack(side=tk.LEFT, padx=5)
        self.triples_tree = ttk.Treeview(tab, columns=('subject', 'predicate', 'object'), show='headings')
        self.triples_tree.heading('subject', text='Subject')
        self.triples_tree.heading('predicate', text='Predicate')
        self.triples_tree.heading('object', text='Object')
        self.triples_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def setup_annotations_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='4. Annotations')
        controls = ttk.Frame(tab)
        controls.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(controls, text="Add Annotation", command=self.add_annotation).pack(side=tk.LEFT)
        ttk.Button(controls, text="Remove Selected", command=self.remove_annotation).pack(side=tk.LEFT, padx=5)
        self.annotations_tree = ttk.Treeview(tab, columns=('construct', 'relation', 'value', 'source'), show='headings')
        self.annotations_tree.heading('construct', text='Construct')
        self.annotations_tree.heading('relation', text='Relation')
        self.annotations_tree.heading('value', text='Value')
        self.annotations_tree.heading('source', text='Source')
        self.annotations_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def save_api_key(self):
        api_key = self.api_key_var.get()
        if not api_key: messagebox.showwarning("Warning", "API Key field is empty."); return
        with open("config.json", 'w') as f: json.dump({"api_key": api_key}, f)
        messagebox.showinfo("Success", "API Key saved.")

    def load_api_key(self):
        if os.path.exists("config.json"):
            with open("config.json", 'r') as f:
                config = json.load(f)
                self.api_key_var.set(config.get("api_key", ""))

    def send_chat_message(self, event=None):
        user_message = self.chat_entry.get()
        if not user_message.strip(): return
        if self.current_theory_id is None: messagebox.showerror("Error", "Please select a theory before starting a chat."); return
        api_key = self.api_key_var.get()
        if not api_key: messagebox.showerror("Error", "API Key is missing. Please set it in the Settings tab."); return
        self._add_text_to_chat(f"You: {user_message}\n")
        self.chat_entry.delete(0, tk.END)
        all_theories_json = json.dumps(self.data_manager.theories, indent=2)
        threading.Thread(target=self._chat_worker, args=(api_key, user_message, all_theories_json, self.current_theory_id), daemon=True).start()

    def _chat_worker(self, api_key, user_message, all_theories_json, current_theory_id):
        processor = LLMProcessor(api_key)
        response = processor.chat(user_message, all_theories_json, current_theory_id)
        if response: self.root.after(0, self._handle_chat_response, response)

    def _handle_chat_response(self, response):
        if "response" in response: self._add_text_to_chat(f"AI: {response['response']}\n\n")
        elif "updated_theory_data" in response:
            updated_data = response['updated_theory_data']
            self._add_text_to_chat("AI: I have updated the theory data as requested. Please review the changes in the tabs and click 'Save Changes for This Theory' to persist them.\n\n")
            self.data_manager.theories[updated_data['id'] - 1] = updated_data
            self.tree.selection_set(str(updated_data['id']))
            self.on_theory_select()
        else: self._add_text_to_chat("AI: I received an unexpected response format. Please try again.\n\n")

    def _add_text_to_chat(self, text):
        self.chat_history.config(state='normal')
        self.chat_history.insert(tk.END, text)
        self.chat_history.config(state='disabled')
        self.chat_history.see(tk.END)

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if path:
            self.current_image_path = path
            self.display_image(path)

    def display_image(self, path):
        if not path or not os.path.exists(path):
            self.image_label.config(image='', text="No Image Selected")
            self.current_image_path = ""
            return
        try:
            self.image_label.update_idletasks()
            w, h = self.image_label.winfo_width(), self.image_label.winfo_height()
            img = Image.open(path)
            img.thumbnail((w - 20, h - 20), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo
        except Exception as e:
            messagebox.showerror("Image Error", f"Could not display image: {e}")
            self.image_label.config(image='', text="Error displaying image")

    def generate_description_with_llm(self):
        if self.current_theory_id is None: messagebox.showerror("Error", "No theory selected."); return
        api_key = self.api_key_var.get()
        if not api_key: messagebox.showerror("Error", "API Key is missing in Settings."); return
        theory_name = self.theory_name_var.get()
        constructs = [{'name': self.constructs_tree.item(i, 'values')[0]} for i in self.constructs_tree.get_children()]
        triples = [{'subject': self.triples_tree.item(i, 'values')[0], 'predicate': self.triples_tree.item(i, 'values')[1], 'object': self.triples_tree.item(i, 'values')[2]} for i in self.triples_tree.get_children()]
        if not constructs and not triples: messagebox.showwarning("Warning", "No constructs or triples to generate a description from."); return
        threading.Thread(target=self._llm_desc_worker, args=(api_key, theory_name, constructs, triples), daemon=True).start()
        messagebox.showinfo("Processing", "Generating description with LLM. This may take a moment.")
        
    def _llm_desc_worker(self, api_key, theory_name, constructs, triples):
        processor = LLMProcessor(api_key)
        description = processor.generate_description(theory_name, constructs, triples)
        if description: self.root.after(0, self.update_description_text, description)

    def update_description_text(self, text):
        self.theory_desc_text.delete(1.0, tk.END)
        self.theory_desc_text.insert(tk.END, text.strip())
        messagebox.showinfo("Success", "Description generated. Please review and save.")

    def on_theory_select(self, event=None):
        selected_item = self.tree.selection()
        if not selected_item: return
        self.current_theory_id = int(selected_item[0])
        theory_data = self.data_manager.get_theory(self.current_theory_id)
        self.set_entry_state('normal')
        self.theory_name_var.set(theory_data.get('name', ''))
        self.theory_desc_text.delete(1.0, tk.END)
        self.theory_desc_text.insert(tk.END, theory_data.get('description', ''))
        self.theory_complete_var.set(theory_data.get('complete', False))
        self.current_image_path = theory_data.get("picture_path", "")
        self.display_image(self.current_image_path)
        self.constructs_tree.delete(*self.constructs_tree.get_children())
        for item in theory_data.get('constructs', []): self.constructs_tree.insert('', 'end', values=(item['name'], item['description']))
        self.triples_tree.delete(*self.triples_tree.get_children())
        for item in theory_data.get('triples', []): self.triples_tree.insert('', 'end', values=(item['subject'], item['predicate'], item['object']))
        self.annotations_tree.delete(*self.annotations_tree.get_children())
        for item in theory_data.get('annotations', []): self.annotations_tree.insert('', 'end', values=(item['construct'], item['relation'], item['value'], item['source']))
        self.chat_history.config(state='normal')
        self.chat_history.delete(1.0, tk.END)
        self.chat_history.insert(tk.END, "Chat with the AI about this theory. You can ask it to make changes.\n\n")
        self.chat_history.config(state='disabled')

    def save_current_theory(self):
        if self.current_theory_id is None: messagebox.showerror("Error", "No theory selected."); return
        constructs = [{'name': self.constructs_tree.item(i, 'values')[0], 'description': self.constructs_tree.item(i, 'values')[1]} for i in self.constructs_tree.get_children()]
        triples = [{'subject': self.triples_tree.item(i, 'values')[0], 'predicate': self.triples_tree.item(i, 'values')[1], 'object': self.triples_tree.item(i, 'values')[2]} for i in self.triples_tree.get_children()]
        annotations = [{'construct': self.annotations_tree.item(i, 'values')[0], 'relation': self.annotations_tree.item(i, 'values')[1], 'value': self.annotations_tree.item(i, 'values')[2], 'source': self.annotations_tree.item(i, 'values')[3]} for i in self.annotations_tree.get_children()]
        updated_data = {"id": self.current_theory_id, "name": self.theory_name_var.get(), "description": self.theory_desc_text.get(1.0, tk.END).strip(), "picture_path": self.current_image_path, "complete": self.theory_complete_var.get(), "constructs": constructs, "triples": triples, "annotations": annotations}
        self.data_manager.update_theory(self.current_theory_id, updated_data)
        self.populate_theory_list()
        messagebox.showinfo("Success", f"Theory '{updated_data['name']}' saved successfully.")

    def populate_theory_list(self):
        self.tree.delete(*self.tree.get_children())
        for theory in self.data_manager.theories:
            status = "Complete" if theory.get('complete') else "Incomplete"
            self.tree.insert('', 'end', text=theory['name'], iid=theory['id'], values=(status,))

    def process_with_llm(self):
        api_key = self.api_key_var.get()
        if not api_key: messagebox.showerror("Error", "API Key is missing."); return
        target_theory_name = self.llm_target_theory_var.get()
        if not target_theory_name: messagebox.showerror("Error", "Please select a target theory."); return
        raw_text = self.llm_input_text.get(1.0, tk.END)
        if not raw_text.strip(): messagebox.showerror("Error", "Input text is empty."); return
        threading.Thread(target=self._llm_worker, args=(api_key, raw_text, target_theory_name), daemon=True).start()
        messagebox.showinfo("Processing", "Sending data to LLM. The UI will be updated upon completion.")

    def _llm_worker(self, api_key, raw_text, target_theory_name):
        processor = LLMProcessor(api_key)
        parsed_data = processor.parse_raw_text(raw_text)
        if parsed_data: self.root.after(0, self.populate_ui_from_llm, parsed_data, target_theory_name)

    def populate_ui_from_llm(self, parsed_data, target_theory_name):
        target_theory_id = next((t['id'] for t in self.data_manager.theories if t['name'] == target_theory_name), None)
        if target_theory_id is None: messagebox.showerror("Error", f"Could not find theory '{target_theory_name}'."); return
        theory_to_update = self.data_manager.get_theory(target_theory_id)
        theory_to_update['constructs'] = parsed_data.get('constructs', [])
        theory_to_update['triples'] = parsed_data.get('triples', [])
        theory_to_update['annotations'] = parsed_data.get('annotations', [])
        self.tree.selection_set(str(target_theory_id))
        self.on_theory_select()
        messagebox.showinfo("Success", f"Data for '{target_theory_name}' has been populated. Review and click 'Save Changes'.")
        self.notebook.select(self.notebook.tabs()[1])
    
    def _recursive_set_state(self, parent, state):
        for child in parent.winfo_children():
            if isinstance(child, ttk.Notebook):
                self._recursive_set_state(child, state)
                continue
            try: child.config(state=state)
            except tk.TclError: pass
            self._recursive_set_state(child, state)

    def set_entry_state(self, state):
        self._recursive_set_state(self.right_frame, state)
        if hasattr(self, 'notebook'):
            for i in range(self.notebook.index("end")):
                try: self.notebook.tab(i, state=state)
                except tk.TclError: pass
    
    def add_construct(self):
        dialog = DataEntryDialog(self.root, "Add Construct", ["Name:", "Description:"])
        if dialog.result: self.constructs_tree.insert('', 'end', values=dialog.result)
            
    def edit_construct(self):
        selected = self.constructs_tree.selection()
        if not selected: return
        values = self.constructs_tree.item(selected[0], 'values')
        dialog = DataEntryDialog(self.root, "Edit Construct", ["Name:", "Description:"], initial_values=values)
        if dialog.result: self.constructs_tree.item(selected[0], values=dialog.result)

    def remove_construct(self):
        selected = self.constructs_tree.selection()
        if selected and messagebox.askyesno("Confirm", "Are you sure?"): self.constructs_tree.delete(selected[0])

    def add_triple(self):
        all_constructs = sorted(list(set([self.constructs_tree.item(i, 'values')[0] for i in self.constructs_tree.get_children()])))
        dialog = DataEntryDialog(self.root, "Add Triple", ["Subject:", "Predicate:", "Object:"], dropdowns={'Subject:': all_constructs, 'Object:': all_constructs})
        if dialog.result: self.triples_tree.insert('', 'end', values=dialog.result)

    def remove_triple(self):
        selected = self.triples_tree.selection()
        if selected and messagebox.askyesno("Confirm", "Are you sure?"): self.triples_tree.delete(selected[0])

    def add_annotation(self):
        all_constructs = sorted(list(set([self.constructs_tree.item(i, 'values')[0] for i in self.constructs_tree.get_children()])))
        dialog = DataEntryDialog(self.root, "Add Annotation", ["Construct:", "Relation:", "Value:", "Source:"], dropdowns={'Construct:': all_constructs})
        if dialog.result: self.annotations_tree.insert('', 'end', values=dialog.result)

    def remove_annotation(self):
        selected = self.annotations_tree.selection()
        if selected and messagebox.askyesno("Confirm", "Are you sure?"): self.annotations_tree.delete(selected[0])
            
    def build_and_visualize(self):
        self.data_manager.build_graph()
        self.data_manager.visualize_graph()

    def export_theory_to_cypher(self):
        """Generates and saves a Cypher script for the current theory."""
        if self.current_theory_id is None:
            messagebox.showerror("Error", "No theory selected to export.")
            return

        theory = self.data_manager.get_theory(self.current_theory_id)
        
        theory_name_raw = theory.get("name", f"Theory_{self.current_theory_id}")
        theory_name_cypher = self._escape_cypher(theory_name_raw)

        safe_filename = re.sub(r'[\\/*?:"<>|]', "", theory_name_raw)
        cypher_lines = [f"// Cypher script for {theory_name_raw}\n\n"]

        cypher_lines.append(f"// Create the main theory node\n")
        cypher_lines.append(f"MERGE (t:Theory {{name: '{theory_name_cypher}'}});\n\n")

        cypher_lines.append(f"// Create construct nodes and add properties\n")
        constructs = theory.get("constructs", [])
        annotations = theory.get("annotations", [])
        
        annotations_by_construct = {}
        for ann in annotations:
            if ann['construct'] not in annotations_by_construct:
                annotations_by_construct[ann['construct']] = []
            annotations_by_construct[ann['construct']].append(ann)

        for construct in constructs:
            name = self._escape_cypher(construct['name'])
            desc = self._escape_cypher(construct.get('description', ''))
            
            props = f"name: '{name}', description: '{desc}'"
            
            if construct['name'] in annotations_by_construct:
                # Get the list of annotation dictionaries for the current construct
                annotations_list = annotations_by_construct[construct['name']]
                # Convert this list into a valid JSON string
                json_string_of_annotations = json.dumps(annotations_list)
                # Escape the entire JSON string for embedding within the Cypher query
                escaped_json_string = self._escape_cypher(json_string_of_annotations)
                
                props += f", annotations: '{escaped_json_string}'"

            cypher_lines.append(f"MERGE (c:Construct {{name: '{name}'}})\nSET c += {{{props}}};\n")

        cypher_lines.append(f"\n// Create relationships from the theory to its constructs\n")
        for construct in constructs:
            c_name = self._escape_cypher(construct['name'])
            cypher_lines.append(f"MATCH (t:Theory {{name: '{theory_name_cypher}'}}), (c:Construct {{name: '{c_name}'}}) MERGE (t)-[:HAS_CONSTRUCT]->(c);\n")
        
        cypher_lines.append(f"\n// Create relationships between constructs based on triples\n")
        for triple in theory.get("triples", []):
            subj = self._escape_cypher(triple['subject'])
            obj = self._escape_cypher(triple['object'])
            pred = re.sub(r'[^a-zA-Z0-9_]', '_', triple['predicate'].upper().replace(" ", "_"))

            cypher_lines.append(f"MATCH (a:Construct {{name: '{subj}'}}), (b:Construct {{name: '{obj}'}}) MERGE (a)-[:{pred}]->(b);\n")
        
        export_dir = "cypher_exports"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
            
        filepath = os.path.join(export_dir, f"{safe_filename}_cypher.cypher")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(cypher_lines)
            
        messagebox.showinfo("Success", f"Cypher script exported successfully to:\n{filepath}")
        
    def _escape_cypher(self, text):
        """Helper function to escape single quotes for Cypher strings."""
        return text.replace("'", "\\'")
        
    def show_incomplete_theories(self):
        """Displays a popup with a list of all incomplete theories."""
        incomplete_theories = [t['name'] for t in self.data_manager.theories if not t.get('complete')]
        
        if not incomplete_theories:
            messagebox.showinfo("All Complete!", "All theories have been marked as complete.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Incomplete Theories")
        popup.geometry("300x400")
        
        label = ttk.Label(popup, text="The following theories are not complete:")
        label.pack(pady=10)
        
        listbox = tk.Listbox(popup)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        for name in incomplete_theories:
            listbox.insert(tk.END, name)

        def go_to_theory(event):
            selected_index = listbox.curselection()
            if not selected_index: return
            name_to_find = listbox.get(selected_index)
            
            for item in self.tree.get_children():
                if self.tree.item(item, 'text') == name_to_find:
                    self.tree.selection_set(item)
                    self.tree.focus(item)
                    self.on_theory_select()
                    popup.destroy()
                    break

        listbox.bind("<Double-1>", go_to_theory)

class DataEntryDialog(simpledialog.Dialog):
    def __init__(self, parent, title, field_labels, initial_values=None, dropdowns=None):
        self.field_labels, self.initial_values, self.dropdowns, self.entries = field_labels, initial_values or [], dropdowns or {}, []
        super().__init__(parent, title)

    def body(self, frame):
        for i, label in enumerate(self.field_labels):
            ttk.Label(frame, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='w')
            initial_val = self.initial_values[i] if i < len(self.initial_values) else ""
            if label in self.dropdowns:
                var = tk.StringVar(value=initial_val)
                entry = ttk.Combobox(frame, textvariable=var, values=self.dropdowns[label], width=47)
                self.entries.append(var)
            else:
                var = tk.StringVar(value=initial_val)
                entry = ttk.Entry(frame, textvariable=var, width=50)
                self.entries.append(var)
            entry.grid(row=i, column=1, padx=5, pady=5)
        return self.entries[0]

    def apply(self):
        self.result = [entry.get() for entry in self.entries]

if __name__ == '__main__':
    root = tk.Tk()
    app = TheoryDataEntryGUI(root)
    root.mainloop()
