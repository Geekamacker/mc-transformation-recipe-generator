from flask import Flask, request, send_file, render_template_string, jsonify
from jinja2 import Template
import os, zipfile, re, logging, json, tempfile, shutil
from datetime import datetime
from werkzeug.utils import secure_filename
import time
from functools import lru_cache
import logging.config

app = Flask(__name__)

# Environment-based configuration
TEMPLATE_PATH = os.getenv("TEMPLATE_PATH", "data/recipe.json.j2")
MASTER_LIST_PATH = os.getenv("MASTER_LIST_PATH", "data/master_list.txt")
LAST_SESSION_PATH = os.getenv("LAST_SESSION_PATH", "data/last_session.json")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
ZIP_PATH = os.getenv("ZIP_PATH", "data/output.zip")
PACK_ICON_PATH = os.getenv("PACK_ICON_PATH", "pack_icon.png")
TEXTURE_DIR = os.getenv("TEXTURE_DIR", "textures/blocks")
PORT = int(os.getenv("PORT", "5097"))
DEBUG_TEMPLATES = os.getenv("DEBUG_TEMPLATES", "false").lower() == "true"

# Filtered items list - easily expandable for future problematic items
FILTERED_ITEMS = {
    'portfolio',  # Causes recipe generation errors - item doesn't exist in Minecraft
    'andesite_wall',
    'axolotl_bucket',
    'balloon',
    'blackstone_wall',
    'bleach',
    'brick_wall',
    'chemical_heat',
    'chipped_anvil',
    'chiseled_bookshelf',
    'chiseled_copper',
    'chiseled_deepslate',
    'chiseled_nether_bricks',
    'chiseled_polished_blackstone',
    'chiseled_quartz_block',
    'chiseled_red_sandstone',
    'chiseled_resin_bricks',
    'chiseled_sandstone',
    'chiseled_stone_bricks',
    'chiseled_tuff',
    'chiseled_tuff_bricks',
    'coal_block',
    'coarse_dirt',
    'cobbled_deepslate_wall',
    'cobblestone_wall',
    'cod_bucket',
    'colored_torch_blue',
    'colored_torch_green',
    'colored_torch_purple',
    'colored_torch_red',
    'compound',
    'compound_creator',
    'cracked_deepslate_bricks',
    'cracked_nether_bricks',
    'cracked_polished_blackstone_bricks',
    'cracked_stone_bricks',
    'cut_copper',
    'cut_copper_slab',
    'cut_copper_stairs',
    'cut_red_sandstone',
    'cut_red_sandstone_slab',
    'cut_sandstone',
    'cut_sandstone_slab',
    'damaged_anvil',
    'deepslate_brick_slab',
    'deepslate_brick_stairs',
    'deepslate_brick_wall',
    'deepslate_bricks',
    'deepslate_tile_wall',
    'diorite_wall',
    'element_0',
    'element_1',
    'element_10',
    'element_100',
    'element_101',
    'element_102',
    'element_103',
    'element_104',
    'element_105',
    'element_106',
    'element_107',
    'element_108',
    'element_109',
    'element_11',
    'element_110',
    'element_111',
    'element_112',
    'element_113',
    'element_114',
    'element_115',
    'element_116',
    'element_117',
    'element_118',
    'element_12',
    'element_13',
    'element_14',
    'element_15',
    'element_16',
    'element_17',
    'element_18',
    'element_19',
    'element_2',
    'element_20',
    'element_21',
    'element_22',
    'element_23',
    'element_24',
    'element_25',
    'element_26',
    'element_27',
    'element_28',
    'element_29',
    'element_3',
    'element_30',
    'element_31',
    'element_32',
    'element_33',
    'element_34',
    'element_35',
    'element_36',
    'element_37',
    'element_38',
    'element_39',
    'element_4',
    'element_40',
    'element_41',
    'element_42',
    'element_43',
    'element_44',
    'element_45',
    'element_46',
    'element_47',
    'element_48',
    'element_49',
    'element_5',
    'element_50',
    'element_51',
    'element_52',
    'element_53',
    'element_54',
    'element_55',
    'element_56',
    'element_57',
    'element_58',
    'element_59',
    'element_6',
    'element_60',
    'element_61',
    'element_62',
    'element_63',
    'element_64',
    'element_65',
    'element_66',
    'element_67',
    'element_68',
    'element_69',
    'element_7',
    'element_70',
    'element_71',
    'element_72',
    'element_73',
    'element_74',
    'element_75',
    'element_76',
    'element_77',
    'element_78',
    'element_79',
    'element_8',
    'element_80',
    'element_81',
    'element_82',
    'element_83',
    'element_84',
    'element_85',
    'element_86',
    'element_87',
    'element_88',
    'element_89',
    'element_9',
    'element_90',
    'element_91',
    'element_92',
    'element_93',
    'element_94',
    'element_95',
    'element_96',
    'element_97',
    'element_98',
    'element_99',
    'element_constructor',
    'end_brick_stairs',
    'end_bricks',
    'end_stone_brick_slab',
    'end_stone_brick_wall',
    'exposed_chiseled_copper',
    'exposed_cut_copper',
    'exposed_cut_copper_slab',
    'exposed_cut_copper_stairs',
    'glow_stick',
    'granite_wall',
    'hard_black_stained_glass',
    'hard_black_stained_glass_pane',
    'hard_blue_stained_glass',
    'hard_blue_stained_glass_pane',
    'hard_brown_stained_glass',
    'hard_brown_stained_glass_pane',
    'hard_cyan_stained_glass',
    'hard_cyan_stained_glass_pane',
    'hard_glass',
    'hard_glass_pane',
    'hard_gray_stained_glass',
    'hard_gray_stained_glass_pane',
    'hard_green_stained_glass',
    'hard_green_stained_glass_pane',
    'hard_light_blue_stained_glass',
    'hard_light_blue_stained_glass_pane',
    'hard_light_gray_stained_glass',
    'hard_light_gray_stained_glass_pane',
    'hard_lime_stained_glass',
    'hard_lime_stained_glass_pane',
    'hard_magenta_stained_glass',
    'hard_magenta_stained_glass_pane',
    'hard_orange_stained_glass',
    'hard_orange_stained_glass_pane',
    'hard_pink_stained_glass',
    'hard_pink_stained_glass_pane',
    'hard_purple_stained_glass',
    'hard_purple_stained_glass_pane',
    'hard_red_stained_glass',
    'hard_red_stained_glass_pane',
    'hard_white_stained_glass',
    'hard_white_stained_glass_pane',
    'hard_yellow_stained_glass',
    'hard_yellow_stained_glass_pane',
    'ice_bomb',
    'infested_chiseled_stone_bricks',
    'infested_cracked_stone_bricks',
    'infested_mossy_stone_bricks',
    'infested_stone_bricks',
    'lab_table',
    'lava_bucket',
    'material_reducer',
    'medicine',
    'milk_bucket',
    'mossy_cobblestone_wall',
    'mossy_stone_brick_slab',
    'mossy_stone_brick_stairs',
    'mossy_stone_brick_wall',
    'mossy_stone_bricks',
    'mud_brick_slab',
    'mud_brick_stairs',
    'mud_brick_wall',
    'mud_bricks',
    'nether_brick',
    'nether_brick_fence',
    'nether_brick_slab',
    'nether_brick_stairs',
    'nether_brick_wall',
    'oxidized_chiseled_copper',
    'oxidized_cut_copper',
    'oxidized_cut_copper_slab',
    'oxidized_cut_copper_stairs',
    'polished_blackstone_brick_slab',
    'polished_blackstone_brick_stairs',
    'polished_blackstone_brick_wall',
    'polished_blackstone_bricks',
    'polished_blackstone_wall',
    'polished_deepslate_wall',
    'polished_tuff_wall',
    'powder_snow_bucket',
    'prismarine_brick_slab',
    'prismarine_bricks',
    'prismarine_bricks_stairs',
    'prismarine_wall',
    'pufferfish_bucket',
    'quartz_bricks',
    'rapid_fertilizer',
    'red_nether_brick',
    'red_nether_brick_slab',
    'red_nether_brick_stairs',
    'red_nether_brick_wall',
    'red_sand',
    'red_sandstone',
    'red_sandstone_slab',
    'red_sandstone_stairs',
    'red_sandstone_wall',
    'resin_brick',
    'resin_brick_slab',
    'resin_brick_stairs',
    'resin_brick_wall',
    'resin_bricks',
    'salmon_bucket',
    'sandstone_wall',
    'smooth_basalt',
    'smooth_quartz',
    'smooth_quartz_slab',
    'smooth_quartz_stairs',
    'smooth_red_sandstone',
    'smooth_red_sandstone_slab',
    'smooth_red_sandstone_stairs',
    'smooth_sandstone',
    'smooth_sandstone_slab',
    'smooth_sandstone_stairs',
    'smooth_stone',
    'smooth_stone_slab',
    'sparkler',
    'stone_brick_slab',
    'stone_brick_stairs',
    'stone_brick_wall',
    'stone_bricks',
    'tadpole_bucket',
    'tropical_fish_bucket',
    'tuff_brick_slab',
    'tuff_brick_stairs',
    'tuff_brick_wall',
    'tuff_bricks',
    'tuff_wall',
    'underwater_tnt',
    'underwater_torch',
    'water_bucket',
    'waxed_chiseled_copper',
    'waxed_cut_copper',
    'waxed_cut_copper_slab',
    'waxed_cut_copper_stairs',
    'waxed_exposed_chiseled_copper',
    'waxed_exposed_cut_copper',
    'waxed_exposed_cut_copper_slab',
    'waxed_exposed_cut_copper_stairs',
    'waxed_oxidized_chiseled_copper',
    'waxed_oxidized_cut_copper',
    'waxed_oxidized_cut_copper_slab',
    'waxed_oxidized_cut_copper_stairs',
    'waxed_weathered_chiseled_copper',
    'waxed_weathered_cut_copper',
    'waxed_weathered_cut_copper_slab',
    'waxed_weathered_cut_copper_stairs',
    'weathered_chiseled_copper',
    'weathered_cut_copper',
    'weathered_cut_copper_slab',
    'weathered_cut_copper_stairs',
    'wet_sponge'
}

# Rate limiting - simple in-memory store (use Redis in production)
download_requests = {}
RATE_LIMIT_REQUESTS = 10  # requests per minute
RATE_LIMIT_WINDOW = 60    # seconds

# Improved logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'default',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['default']
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Load HTML template
try:
    with open("index.html") as f:
        HTML_TEMPLATE = f.read()
        logger.info("HTML template loaded successfully")
except FileNotFoundError:
    logger.error("index.html not found, using basic template")
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html><head><title>Recipe Generator</title></head>
    <body>
    <h1>Recipe Generator</h1>
    <p>Error: index.html template not found</p>
    <div>{{ message|safe }}</div>
    <div>{{ error }}</div>
    </body></html>
    """

@lru_cache(maxsize=1)
def load_template():
    """Load and cache the Jinja2 template"""
    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            if DEBUG_TEMPLATES:
                logger.info(f"Template loaded from: {TEMPLATE_PATH}")
                logger.info(f"Template content preview: {content[:200]}...")
            return Template(content)
    except FileNotFoundError:
        logger.error(f"Template file not found: {TEMPLATE_PATH}")
        raise
    except Exception as e:
        logger.error(f"Error loading template: {e}")
        raise

def safe_file_write(file_path, content):
    """Safely write content to file with proper error handling"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Failed to write file {file_path}: {e}")
        return False

def safe_filename(name):
    """Create safe filename from item name"""
    if not name or not isinstance(name, str):
        raise ValueError("Invalid item name")
    
    # Remove dangerous characters and limit length
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name.strip())
    if len(safe_name) > 50:
        safe_name = safe_name[:50]
    
    if not safe_name:
        raise ValueError("Item name results in empty filename")
    
    return safe_name

def validate_item_names(items):
    """Validate a list of item names"""
    if not isinstance(items, list):
        raise ValueError("Items must be a list")
    
    validated_items = []
    for item in items:
        if not isinstance(item, str):
            continue
        
        item = item.strip()
        if not item:
            continue
            
        # Check for reasonable length and characters
        if len(item) > 100:
            raise ValueError(f"Item name too long: {item}")
        
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', item):
            raise ValueError(f"Invalid characters in item name: {item}")
        
        validated_items.append(item)
    
    return validated_items

def check_rate_limit(client_ip):
    """Simple rate limiting"""
    now = time.time()
    
    # Clean old requests
    cutoff = now - RATE_LIMIT_WINDOW
    download_requests[client_ip] = [req_time for req_time in download_requests.get(client_ip, []) if req_time > cutoff]
    
    # Check if over limit
    if len(download_requests.get(client_ip, [])) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Add current request
    if client_ip not in download_requests:
        download_requests[client_ip] = []
    download_requests[client_ip].append(now)
    
    return True

def load_last_session():
    """Load the user's last session data"""
    try:
        if os.path.exists(LAST_SESSION_PATH):
            with open(LAST_SESSION_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Validate loaded data
            if not isinstance(data, dict):
                raise ValueError("Invalid session data format")
            
            items = validate_item_names(data.get("items", []))
            selected = validate_item_names(data.get("selected", []))
            
            return {
                "items": items,
                "selected": selected,
                "timestamp": data.get("timestamp")
            }
    except (json.JSONDecodeError, IOError, ValueError) as e:
        logger.warning(f"Could not load last session data: {e}")
    
    return {"items": [], "selected": [], "timestamp": None}

def save_session(items, selected_items):
    """Save the current session data"""
    try:
        # Validate inputs
        items = validate_item_names(items)
        selected_items = validate_item_names(selected_items)
        
        session_data = {
            "items": items,
            "selected": selected_items,
            "timestamp": datetime.now().isoformat()
        }
        
        os.makedirs("data", exist_ok=True)
        
        # Write to temporary file first, then rename (atomic operation)
        temp_path = LAST_SESSION_PATH + ".tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        os.replace(temp_path, LAST_SESSION_PATH)
        logger.info(f"Session saved: {len(items)} items, {len(selected_items)} selected")
        
    except (IOError, ValueError) as e:
        logger.error(f"Could not save session data: {e}")
        raise

def get_all_items():
    """Get all items from master list"""
    try:
        if os.path.exists(MASTER_LIST_PATH):
            with open(MASTER_LIST_PATH, 'r', encoding='utf-8') as f:
                items = [line.strip() for line in f if line.strip()]
            return validate_item_names(items)
    except (IOError, ValueError) as e:
        logger.warning(f"Could not read master list: {e}")
    
    return []

def cleanup_old_files():
    """Clean up old temporary files"""
    try:
        if os.path.exists(OUTPUT_DIR):
            for f_name in os.listdir(OUTPUT_DIR):
                file_path = os.path.join(OUTPUT_DIR, f_name)
                if os.path.isfile(file_path):
                    # Remove files older than 1 hour
                    if time.time() - os.path.getmtime(file_path) > 3600:
                        os.remove(file_path)
    except Exception as e:
        logger.warning(f"Error cleaning up old files: {e}")

def clean_item_name(item_string):
    """Clean item name by removing minecraft: prefix and other formatting"""
    if not item_string or not isinstance(item_string, str):
        return None
    
    # Remove quotes
    item_string = item_string.strip('"\'')
    
    # Remove minecraft: prefix
    if item_string.startswith('minecraft:'):
        item_string = item_string[10:]  # Remove 'minecraft:' (10 characters)
    
    # Remove any trailing data after : (like damage values)
    if ':' in item_string:
        item_string = item_string.split(':')[0]
    
    # Remove any whitespace
    item_string = item_string.strip()
    
    # Filter out problematic items
    if item_string.lower() in FILTERED_ITEMS:
        logger.debug(f"Filtered out problematic item: {item_string}")
        return None
    
    # Validate item name (only allow valid Minecraft item characters)
    if re.match(r'^[a-z0-9_]+$', item_string):
        return item_string
    
    return None

def parse_json_catalog(content):
    """Parse JSON catalog file and extract item names"""
    try:
        data = json.loads(content)
        items = []
        
        def extract_items_recursive(obj):
            """Recursively extract items from nested JSON structure"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "items" and isinstance(value, list):
                        for item in value:
                            if isinstance(item, str):
                                clean_item = clean_item_name(item)
                                if clean_item:
                                    items.append(clean_item)
                    else:
                        extract_items_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_items_recursive(item)
        
        extract_items_recursive(data)
        return items
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON format")
        return []

def parse_text_catalog(content):
    """Parse text file and extract item names"""
    items = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('//'):
            clean_item = clean_item_name(line)
            if clean_item:
                items.append(clean_item)
    
    return items

@app.before_request
def validate_request():
    """Validate incoming requests"""
    # Limit request size to 10MB
    if request.content_length and request.content_length > 10 * 1024 * 1024:
        return "Request too large", 413

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "template_exists": os.path.exists(TEMPLATE_PATH)
    })

@app.route("/upload-catalog", methods=["POST"])
def upload_catalog():
    """Handle multiple catalog file uploads and extract item names"""
    try:
        # Handle both single file and multiple files
        files = request.files.getlist('catalog_file')
        
        if not files or (len(files) == 1 and files[0].filename == ''):
            return jsonify({"success": False, "error": "No files uploaded"})
        
        all_extracted_items = []
        processed_files = []
        failed_files = []
        
        for file in files:
            if file.filename == '':
                continue
                
            try:
                # Read file content
                file_content = file.read().decode('utf-8')
                
                # Parse and extract items based on file type
                file_items = []
                
                if file.filename.lower().endswith('.json'):
                    file_items = parse_json_catalog(file_content)
                elif file.filename.lower().endswith('.txt'):
                    file_items = parse_text_catalog(file_content)
                else:
                    failed_files.append(f"{file.filename} (unsupported format)")
                    continue
                
                if file_items:
                    all_extracted_items.extend(file_items)
                    processed_files.append(f"{file.filename} ({len(file_items)} items)")
                    logger.info(f"Successfully extracted {len(file_items)} items from {file.filename}")
                else:
                    failed_files.append(f"{file.filename} (no valid items found)")
                    
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {e}")
                failed_files.append(f"{file.filename} (processing error)")
                continue
        
        if not all_extracted_items:
            return jsonify({"success": False, "error": "No valid items found in any of the uploaded files"})
        
        # Remove duplicates and sort
        unique_items = sorted(list(set(all_extracted_items)))
        
        # Build success message
        message_parts = []
        if processed_files:
            message_parts.append(f"Successfully processed {len(processed_files)} file(s)")
            message_parts.append(f"Found {len(unique_items)} unique items")
            message_parts.append(f"Ready to use: {len(unique_items)} items")
        
        message = ". ".join(message_parts)
        
        response_data = {
            "success": True, 
            "items": unique_items,
            "count": len(unique_items),
            "total_items": len(all_extracted_items),
            "unique_items": len(unique_items),
            "filtered_items": 0,
            "processed_files": processed_files,
            "failed_files": failed_files,
            "message": message
        }
        
        if failed_files:
            response_data["warning"] = f"Some files could not be processed: {', '.join(failed_files)}"
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing catalog uploads: {e}")
        return jsonify({"success": False, "error": "Failed to process the uploaded files"})

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    error = ""
    
    # Load last session for display
    last_session = load_last_session()
    
    if request.method == "POST":
        try:
            action = request.form.get("action", "generate")
            
            if action == "load_last":
                if last_session["items"]:
                    items_text = "\n".join(last_session["items"])
                    selected_items = last_session["selected"]
                    
                    js_script = f"""
                    <script>
                    document.addEventListener('DOMContentLoaded', function() {{
                        document.getElementById('textarea').value = {json.dumps(items_text)};
                        document.getElementById('convertBtn').click();
                        
                        setTimeout(function() {{
                            const selectedItems = {json.dumps(selected_items)};
                            document.querySelectorAll('#checklist input[type="checkbox"]').forEach(cb => {{
                                cb.checked = selectedItems.includes(cb.value);
                            }});
                            updatePreview();
                        }}, 100);
                    }});
                    </script>
                    """
                    
                    timestamp = datetime.fromisoformat(last_session["timestamp"]).strftime("%Y-%m-%d %H:%M:%S") if last_session["timestamp"] else "Unknown"
                    message = f"Last session loaded (from {timestamp}). {js_script}"
                else:
                    message = "No previous session found."
                    
                return render_template_string(HTML_TEMPLATE, message=message, error=error)
            
            # Handle normal form submission - Generate recipes
            submitted_items = request.form.getlist("selected")
            all_items_raw = request.form.get("all_items", "")
            
            if not submitted_items:
                error = "No items selected. Please select at least one item."
                return render_template_string(HTML_TEMPLATE, message=message, error=error)
            
            # Validate inputs
            submitted_items = validate_item_names(submitted_items)
            all_items = validate_item_names(all_items_raw.split("\n") if all_items_raw else [])
            
            if not submitted_items:
                error = "No items selected. Please select at least one item."
                return render_template_string(HTML_TEMPLATE, message=message, error=error)
            
            # Sort the items to ensure consistent order
            submitted_items.sort()
            
            logger.info(f"Form submission: {len(submitted_items)} items selected, {len(all_items)} total items")
            
            # Clean up old files
            cleanup_old_files()
            
            # Ensure directories exist
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            os.makedirs("data", exist_ok=True)

            # Load template (cached)
            template = load_template()

            # Clear output directory
            for f_name in os.listdir(OUTPUT_DIR):
                file_path = os.path.join(OUTPUT_DIR, f_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)

            # Update master list safely
            try:
                master_items = set()
                if os.path.exists(MASTER_LIST_PATH):
                    with open(MASTER_LIST_PATH, 'r', encoding='utf-8') as f:
                        master_items = set(line.strip().lower() for line in f if line.strip())

                new_items = [item for item in submitted_items if item.lower() not in master_items]
                if new_items:
                    with open(MASTER_LIST_PATH, "a", encoding='utf-8') as f:
                        for item in new_items:
                            f.write(item + "\n")
            except Exception as e:
                logger.warning(f"Could not update master list: {e}")

            # Generate recipe files - SEQUENTIAL TRANSFORMATION
            generated_files = []
            for i in range(len(submitted_items) - 1):  # Stop at second-to-last item
                try:
                    input_item = submitted_items[i]
                    result_item = submitted_items[i + 1]  # Next item in the list
                    
                    if DEBUG_TEMPLATES:
                        logger.info(f"Processing: {input_item} → {result_item}")
                    
                    safe_input = safe_filename(input_item)
                    safe_result = safe_filename(result_item)
                    
                    rendered = template.render(input_item=input_item, result_item=result_item)
                    
                    if DEBUG_TEMPLATES:
                        logger.info(f"Rendered result preview: {rendered[:200]}...")
                    
                    filename = f"{safe_input}_to_{safe_result}.json"
                    file_path = os.path.join(OUTPUT_DIR, filename)
                    
                    if safe_file_write(file_path, rendered):
                        generated_files.append(filename)
                        logger.info(f"Generated: {filename} ({input_item} → {result_item})")
                    else:
                        logger.error(f"Failed to write: {filename}")
                    
                except Exception as e:
                    logger.error(f"Error generating recipe for {input_item} → {result_item}: {e}")
                    continue
            
            # Add the cycle-back recipe (last item → first item)
            if len(submitted_items) >= 2:
                try:
                    input_item = submitted_items[-1]  # Last item
                    result_item = submitted_items[0]   # First item
                    
                    safe_input = safe_filename(input_item)
                    safe_result = safe_filename(result_item)
                    
                    rendered = template.render(input_item=input_item, result_item=result_item)
                    filename = f"{safe_input}_to_{safe_result}.json"
                    file_path = os.path.join(OUTPUT_DIR, filename)
                    
                    if safe_file_write(file_path, rendered):
                        generated_files.append(filename)
                        logger.info(f"Generated cycle-back: {filename} ({input_item} → {result_item})")
                    
                except Exception as e:
                    logger.error(f"Error generating cycle-back recipe for {input_item} → {result_item}: {e}")

            # Always add the transformation table crafting recipe
            try:
                table_recipe_content = """{
    "format_version": "1.12",
    "minecraft:recipe_shaped": {
        "description": {
            "identifier": "transformationtable:transformation_table"
        },
        "tags": [
            "crafting_table"
        ],
        "pattern": [
            "iDi",
            "iCi",
            "iii"
        ],
        "key": {
            "i": {
                "item": "minecraft:iron_ingot"
            },
            "D": {
                "item": "minecraft:diamond"
            },
            "C": {
                "item": "minecraft:crafting_table"
            }
        },
        "result": {
            "item": "transformationtable:transformation_table",
            "count": 1
        }
    }
}"""
                
                table_recipe_filename = "transformation_table.json"
                table_recipe_path = os.path.join(OUTPUT_DIR, table_recipe_filename)
                
                if safe_file_write(table_recipe_path, table_recipe_content):
                    generated_files.append(table_recipe_filename)
                    logger.info("Added transformation table crafting recipe to output")
                
            except Exception as e:
                logger.error(f"Error adding table recipe: {e}")

            if not generated_files:
                error = "No recipe files were generated successfully."
                return render_template_string(HTML_TEMPLATE, message=message, error=error)

            # Create ZIP file safely
            temp_zip = ZIP_PATH + ".tmp"
            try:
                with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for filename in generated_files:
                        file_path = os.path.join(OUTPUT_DIR, filename)
                        if os.path.exists(file_path):
                            zipf.write(file_path, arcname=filename)
                            logger.info(f"Added to ZIP: {filename}")
                
                # Atomic rename
                if os.path.exists(ZIP_PATH):
                    os.remove(ZIP_PATH)
                os.rename(temp_zip, ZIP_PATH)
                
            except Exception as e:
                logger.error(f"Error creating ZIP file: {e}")
                if os.path.exists(temp_zip):
                    os.remove(temp_zip)
                error = "Failed to create download package."
                return render_template_string(HTML_TEMPLATE, message=message, error=error)

            if not os.path.exists(ZIP_PATH) or os.path.getsize(ZIP_PATH) == 0:
                error = "ZIP file creation failed or is empty."
                logger.error(error)
                return render_template_string(HTML_TEMPLATE, message=message, error=error)

            # Save current session
            try:
                save_session(all_items, submitted_items)
            except Exception as e:
                logger.warning(f"Could not save session: {e}")

            zip_size = os.path.getsize(ZIP_PATH)
            message = f"✅ Successfully generated {len(generated_files)-1} transformation recipe(s) from {len(submitted_items)} items ({zip_size:,} bytes). <a href='/download' style='color: #90ee90; text-decoration: underline;'>Download ZIP</a>"
            logger.info(f"ZIP created successfully: {zip_size} bytes")

        except ValueError as e:
            error = f"Invalid input: {str(e)}"
            logger.error(f"Validation error: {e}")
        except Exception as e:
            error = f"An unexpected error occurred. Please try again."
            logger.error(f"Error in recipe generation: {e}", exc_info=True)

    return render_template_string(HTML_TEMPLATE, message=message, error=error)

@app.route("/download-custom", methods=["POST"])
def download_custom():
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    
    # Rate limiting
    if not check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for {client_ip}")
        return "Too many requests. Please wait before downloading again.", 429
    
    try:
        format_type = request.form.get('format', 'standard')
        items_json = request.form.get('items', '[]')
        
        # Validate format type
        valid_formats = ['standard', 'datapack', 'behavior_pack', 'complete_pack', 'custom']
        if format_type not in valid_formats:
            return "Invalid format type", 400
        
        try:
            selected_items = json.loads(items_json)
            selected_items = validate_item_names(selected_items)
            selected_items.sort()
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Invalid items JSON: {e}")
            return "Invalid items data", 400
        
        logger.info(f"Custom download requested: format={format_type}, items={len(selected_items)}")
        
        # Add progress logging for large batches
        if len(selected_items) > 500:
            logger.info(f"Processing large batch of {len(selected_items)} items - this may take a moment...")
        
        if not selected_items:
            return "No items selected", 400
            
        if len(selected_items) < 2:
            return "Need at least 2 items to create transformation chain", 400
            
        # Keep the 5000 limit as requested
        if len(selected_items) > 5000:
            return "Too many items selected. Please select fewer than 5000 items for performance reasons.", 400
            
        # Ensure directories exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs("data", exist_ok=True)
        
        # Load cached template
        template = load_template()
        
        # Clean up old files
        cleanup_old_files()
        
        # Create custom structure based on format  
        # Use temp directory for better isolation
        import tempfile
        temp_dir = tempfile.gettempdir()
        custom_zip_path = os.path.join(temp_dir, f"custom_{format_type}_{int(time.time())}.zip")
        
        try:
            with zipfile.ZipFile(custom_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Generate recipe files - SEQUENTIAL TRANSFORMATION
                successful_recipes = 0
                failed_recipes = 0
                
                for i in range(len(selected_items) - 1):  # Stop at second-to-last item
                    try:
                        input_item = selected_items[i]
                        result_item = selected_items[i + 1]  # Next item in the list
                        
                        safe_input = safe_filename(input_item)
                        safe_result = safe_filename(result_item)
                        
                        rendered = template.render(input_item=input_item, result_item=result_item)
                        filename = f"{safe_input}_to_{safe_result}.json"
                        
                        # Determine file path based on format
                        if format_type == 'datapack':
                            arcname = f"data/transformation/recipes/{filename}"
                        elif format_type == 'behavior_pack':
                            arcname = f"Transformation Table BP/recipes/{filename}"
                        elif format_type == 'complete_pack':
                            arcname = f"Transformation Table BP/recipes/{filename}"
                        elif format_type == 'custom':
                            category = get_item_category(input_item)
                            arcname = f"{category}/{filename}"
                        else:
                            arcname = filename
                        
                        zipf.writestr(arcname, rendered)
                        successful_recipes += 1
                        
                        # Log progress for large batches
                        if len(selected_items) > 500 and (i + 1) % 100 == 0:
                            logger.info(f"Progress: {i + 1}/{len(selected_items)-1} recipes generated")
                        
                    except Exception as e:
                        logger.error(f"Error processing item {input_item} → {result_item}: {e}")
                        failed_recipes += 1
                        continue
                
                # Add the cycle-back recipe (last item → first item)
                if len(selected_items) >= 2:
                    try:
                        input_item = selected_items[-1]  # Last item
                        result_item = selected_items[0]   # First item
                        
                        safe_input = safe_filename(input_item)
                        safe_result = safe_filename(result_item)
                        
                        rendered = template.render(input_item=input_item, result_item=result_item)
                        filename = f"{safe_input}_to_{safe_result}.json"
                        
                        # Determine file path based on format
                        if format_type == 'datapack':
                            arcname = f"data/transformation/recipes/{filename}"
                        elif format_type == 'behavior_pack':
                            arcname = f"Transformation Table BP/recipes/{filename}"
                        elif format_type == 'complete_pack':
                            arcname = f"Transformation Table BP/recipes/{filename}"
                        elif format_type == 'custom':
                            category = get_item_category(input_item)
                            arcname = f"{category}/{filename}"
                        else:
                            arcname = filename
                        
                        zipf.writestr(arcname, rendered)
                        successful_recipes += 1
                        logger.info(f"Added cycle-back recipe: {input_item} → {result_item}")
                        
                    except Exception as e:
                        logger.error(f"Error processing cycle-back recipe {input_item} → {result_item}: {e}")
                        failed_recipes += 1
                
                logger.info(f"Recipe generation complete: {successful_recipes} successful, {failed_recipes} failed")
                
                # ALWAYS add the transformation table crafting recipe for behavior packs and complete packs
                if format_type in ['behavior_pack', 'complete_pack']:
                    try:
                        table_recipe_content = """{
    "format_version": "1.12",
    "minecraft:recipe_shaped": {
        "description": {
            "identifier": "transformationtable:transformation_table"
        },
        "tags": [
            "crafting_table"
        ],
        "pattern": [
            "iDi",
            "iCi",
            "iii"
        ],
        "key": {
            "i": {
                "item": "minecraft:iron_ingot"
            },
            "D": {
                "item": "minecraft:diamond"
            },
            "C": {
                "item": "minecraft:crafting_table"
            }
        },
        "result": {
            "item": "transformationtable:transformation_table",
            "count": 1
        }
    }
}"""
                        
                        if format_type == 'behavior_pack':
                            table_recipe_arcname = "Transformation Table BP/recipes/transformation_table.json"
                        elif format_type == 'complete_pack':
                            table_recipe_arcname = "Transformation Table BP/recipes/transformation_table.json"
                        
                        zipf.writestr(table_recipe_arcname, table_recipe_content)
                        successful_recipes += 1
                        logger.info("Added transformation table crafting recipe to pack")
                        
                    except Exception as e:
                        logger.error(f"Error adding table recipe to pack: {e}")
                        failed_recipes += 1
                        
                # Add metadata files based on format
                try:
                    if format_type == 'datapack':
                        add_datapack_metadata(zipf)
                    elif format_type == 'behavior_pack':
                        add_behavior_pack_metadata(zipf)
                    elif format_type == 'complete_pack':
                        add_complete_pack_metadata(zipf)
                    elif format_type == 'custom':
                        add_custom_metadata(zipf, selected_items)
                except Exception as e:
                    logger.error(f"Error adding metadata: {e}")
        
        except Exception as e:
            logger.error(f"Error creating custom ZIP: {e}")
            if os.path.exists(custom_zip_path):
                os.remove(custom_zip_path)
            return "Error creating download package", 500
        
        if not os.path.exists(custom_zip_path) or os.path.getsize(custom_zip_path) == 0:
            logger.error("Custom ZIP creation failed or empty")
            return "Download package creation failed", 500
        
        zip_size = os.path.getsize(custom_zip_path)
        logger.info(f"Custom ZIP created: {custom_zip_path} ({zip_size:,} bytes)")
        
        # Clean up file after sending
        def remove_file():
            try:
                if os.path.exists(custom_zip_path):
                    os.remove(custom_zip_path)
            except:
                pass
        
        # Schedule cleanup (simple approach - use Celery in production)
        import threading
        cleanup_timer = threading.Timer(300, remove_file)  # Clean up after 5 minutes
        cleanup_timer.start()
        
        # Set proper download filename based on format
        if format_type == 'behavior_pack':
            download_filename = 'Transformation_Table_BP.zip'
        elif format_type == 'complete_pack':
            download_filename = 'Transformation_Table_Complete_Pack.zip'
        else:
            download_filename = f"minecraft_transformation_recipes_{format_type}.zip"
        
        return send_file(custom_zip_path, as_attachment=True, 
                        download_name=download_filename, 
                        mimetype='application/zip')
                        
    except Exception as e:
        logger.error(f"Error in custom download: {e}", exc_info=True)
        return "Internal server error", 500

def get_item_category(item):
    """Categorize items for custom folder structure"""
    if not item:
        return 'misc'
    
    item_lower = item.lower()
    
    if any(word in item_lower for word in ['ore', 'raw_']):
        return 'ores'
    elif any(word in item_lower for word in ['ingot', 'nugget']):
        return 'metals'
    elif any(word in item_lower for word in ['wood', 'log', 'plank']):
        return 'wood'
    elif any(word in item_lower for word in ['stone', 'cobble', 'granite', 'diorite']):
        return 'stone'
    elif any(word in item_lower for word in ['diamond', 'emerald', 'ruby', 'sapphire']):
        return 'gems'
    elif any(word in item_lower for word in ['food', 'bread', 'meat', 'apple']):
        return 'food'
    else:
        return 'misc'

def add_datapack_metadata(zipf):
    """Add pack.mcmeta for Java datapack"""
    logger.info("Adding datapack metadata...")
    pack_mcmeta = {
        "pack": {
            "pack_format": 10,
            "description": "Transformation Recipes Datapack"
        }
    }
    zipf.writestr("pack.mcmeta", json.dumps(pack_mcmeta, indent=2))

def add_behavior_pack_metadata(zipf):
    """Add manifest.json and pack structure for Bedrock behavior pack"""
    logger.info("Adding behavior pack metadata...")
    
    # FIXED: Using the exact same UUIDs as your working uncrafting table pack
    manifest = {
        "format_version": 2,
        "metadata": {
            "authors": ["foamwrap"]
        },
        "header": {
            "name": "Transformation Table",
            "description": "By foamwrap",
            "min_engine_version": [1, 20, 60],
            "uuid": "b6f04080-1c3d-4bc0-b8f2-4624078d108f",  # Same as uncrafting table structure
            "version": [3, 0, 0]
        },
        "modules": [
            {
                "type": "data",
                "uuid": "56df8307-2bf9-4a4e-a7d6-fe057ed5a075",  # Same as uncrafting table structure
                "version": [3, 0, 0]
            }
        ],
        "dependencies": [
            {
                "uuid": "54ac9ad2-a9c7-4596-bacb-73336ba88451",  # Same as uncrafting table structure
                "version": [3, 0, 0]
            }
        ]
    }
    zipf.writestr("Transformation Table BP/manifest.json", json.dumps(manifest, indent=4))
    
    # FIXED: Block definition matching your working uncrafting table exactly
    transformation_table_block = {
        "format_version": "1.20.60",
        "minecraft:block": {
            "description": {
                "identifier": "transformationtable:transformation_table",
                "menu_category": {
                    "category": "equipment"
                },
                "is_experimental": False,
                "traits": {
                    "minecraft:placement_direction": {
                        "enabled_states": ["minecraft:cardinal_direction"]
                    }
                }
            },
            "components": {
                "minecraft:crafting_table": {
                    "crafting_tags": ["transformation_table"],  # Fixed to match identifier
                    "grid_size": 3,
                    "table_name": "Transformation"
                },
                "minecraft:collision_box": {
                    "size": [16, 16, 16],
                    "origin": [-8, 0, -8]
                },
                "minecraft:geometry": "geometry.transformation_table",
                "minecraft:material_instances": {
                    "up": {
                        "texture": "tt_top",
                        "render_method": "opaque"
                    },
                    "*": {
                        "texture": "tt_side",
                        "render_method": "opaque"
                    },
                    "north": {
                        "texture": "tt_front",
                        "render_method": "opaque"
                    }
                },
                "minecraft:flammable": True,  # Fixed: should be boolean, not string
                "minecraft:destructible_by_mining": {
                    "seconds_to_destroy": 1
                },
                "minecraft:destructible_by_explosion": {
                    "explosion_resistance": 7.5
                },
                "minecraft:selection_box": {
                    "origin": [-8, 0, -8],
                    "size": [16, 16, 16]
                }
            },
            "permutations": [
                {
                    "condition": "query.block_state('minecraft:cardinal_direction')=='south'",
                    "components": {
                        "minecraft:transformation": {
                            "rotation": [0, 0, 0]
                        }
                    }
                },
                {
                    "condition": "query.block_state('minecraft:cardinal_direction')=='east'",
                    "components": {
                        "minecraft:transformation": {
                            "rotation": [0, 90, 0]
                        }
                    }
                },
                {
                    "condition": "query.block_state('minecraft:cardinal_direction')=='west'",
                    "components": {
                        "minecraft:transformation": {
                            "rotation": [0, -90, 0]
                        }
                    }
                },
                {
                    "condition": "query.block_state('minecraft:cardinal_direction')=='north'",
                    "components": {
                        "minecraft:transformation": {
                            "rotation": [0, 180, 0]
                        }
                    }
                }
            ]
        }
    }
    zipf.writestr("Transformation Table BP/blocks/transformation_table.json", 
                  json.dumps(transformation_table_block, indent=2))
    
    # Copy pack icon
    try:
        if os.path.exists(PACK_ICON_PATH):
            with open(PACK_ICON_PATH, 'rb') as icon_file:
                pack_icon_content = icon_file.read()
            zipf.writestr("Transformation Table BP/pack_icon.png", pack_icon_content)
            logger.info(f"Added pack icon from {PACK_ICON_PATH} (size: {len(pack_icon_content)} bytes)")
        else:
            logger.warning(f"Pack icon not found at {PACK_ICON_PATH}")
    except Exception as e:
        logger.error(f"Error adding pack icon: {e}")
    
    logger.info("Behavior pack metadata complete")

def add_complete_pack_metadata(zipf):
    """Add both Behavior Pack and Resource Pack metadata and files"""
    logger.info("Adding complete pack metadata (BP + RP)...")
    
    try:
        # First add the Behavior Pack components
        add_behavior_pack_metadata(zipf)
        logger.info("Behavior Pack metadata added successfully")
    except Exception as e:
        logger.error(f"Error adding behavior pack metadata: {e}")
        raise
    
    try:
        # RP Manifest
        rp_manifest = {
            "format_version": 2,
            "metadata": {"authors": ["foamwrap"]},
            "header": {
                "name": "Transformation Table",
                "description": "By foamwrap",
                "min_engine_version": [1, 20, 60],
                "uuid": "54ac9ad2-a9c7-4596-bacb-73336ba88451",
                "version": [3, 0, 0]
            },
            "modules": [
                {
                    "type": "resources",
                    "uuid": "d1e248e1-bcd8-4bfe-b632-650602f94f32",
                    "version": [3, 0, 0]
                }
            ],
            "dependencies": [
                {
                    "uuid": "b6f04080-1c3d-4bc0-b8f2-4624078d108f",
                    "version": [3, 0, 0]
                }
            ]
        }
        zipf.writestr("Transformation Table RP/manifest.json", json.dumps(rp_manifest, indent=4))
        logger.info("RP manifest added successfully")
    except Exception as e:
        logger.error(f"Error adding RP manifest: {e}")
        raise
    
    try:
        # FIXED: RP blocks.json with correct namespace to match your working example
        rp_blocks = {
            "format_version": [1, 1, 0],
            "transformationtable:transformation_table": {  # FIXED: Match the block identifier
                "sound": "wood",
                "textures": {
                    "up": "tt_top",
                    "side": "tt_side"
                }
            }
        }
        zipf.writestr("Transformation Table RP/blocks.json", json.dumps(rp_blocks, indent=4))
        logger.info("RP blocks.json added successfully")
    except Exception as e:
        logger.error(f"Error adding RP blocks.json: {e}")
        raise
    
    try:
        # Language files
        zipf.writestr("Transformation Table RP/texts/languages.json", '[\n\t"en_US"\n]')
        zipf.writestr("Transformation Table RP/texts/en_US.lang", 
                      "tile.transformationtable:transformation_table.name=Transformation Table")
        logger.info("Language files added successfully")
    except Exception as e:
        logger.error(f"Error adding language files: {e}")
        raise
    
    try:
        # Terrain texture
        terrain_texture = {
            "num_mip_levels": 4,
            "padding": 8,
            "resource_pack_name": "Transformation Table",
            "texture_name": "atlas.terrain",
            "texture_data": {
                "tt_side": {
                    "textures": "textures/blocks/transformation_table_side"
                },
                "tt_top": {
                    "textures": "textures/blocks/transformation_table_top"
                },
                "tt_front": {
                    "textures": "textures/blocks/transformation_table_front"
                }
            }
        }
        zipf.writestr("Transformation Table RP/textures/terrain_texture.json", 
                      json.dumps(terrain_texture, indent=4))
        logger.info("Terrain texture added successfully")
    except Exception as e:
        logger.error(f"Error adding terrain texture: {e}")
        raise
    
    try:
        # Geometry
        geometry = {
            "format_version": "1.12.0",
            "minecraft:geometry": [
                {
                    "description": {
                        "identifier": "geometry.transformation_table",
                        "texture_width": 16,
                        "texture_height": 16,
                        "visible_bounds_width": 2,
                        "visible_bounds_height": 2.5,
                        "visible_bounds_offset": [0, 0.75, 0]
                    },
                    "bones": [
                        {
                            "name": "root",
                            "pivot": [0, 0, 0],
                            "cubes": [
                                {
                                    "origin": [-8, 0, -8],
                                    "size": [16, 16, 16],
                                    "uv": {
                                        "north": {"uv": [0, 0], "uv_size": [16, 16], "material_instance": "north"},
                                        "east": {"uv": [0, 0], "uv_size": [16, 16], "material_instance": "east"},
                                        "south": {"uv": [0, 0], "uv_size": [16, 16], "material_instance": "south"},
                                        "west": {"uv": [0, 0], "uv_size": [16, 16], "material_instance": "west"},
                                        "up": {"uv": [16, 16], "uv_size": [-16, -16], "material_instance": "up"},
                                        "down": {"uv": [16, 16], "uv_size": [-16, -16], "material_instance": "down"}
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        zipf.writestr("Transformation Table RP/models/blocks/transformation_table.geo.json", 
                      json.dumps(geometry, indent=4))
        logger.info("Geometry added successfully")
    except Exception as e:
        logger.error(f"Error adding geometry: {e}")
        raise
    
    try:
        # Copy pack icon to RP as well
        if os.path.exists(PACK_ICON_PATH):
            with open(PACK_ICON_PATH, 'rb') as icon_file:
                pack_icon_content = icon_file.read()
            zipf.writestr("Transformation Table RP/pack_icon.png", pack_icon_content)
            logger.info("Added pack icon to Resource Pack")
        else:
            logger.warning(f"Pack icon not found at {PACK_ICON_PATH}")
    except Exception as e:
        logger.error(f"Error adding RP pack icon: {e}")
        # Don't raise, continue without icon
    
    # Add real texture files with detailed logging
    texture_files = [
        ('textures/blocks/transformation_table_front.png', 'Transformation Table RP/textures/blocks/transformation_table_front.png'),
        ('textures/blocks/transformation_table_side.png', 'Transformation Table RP/textures/blocks/transformation_table_side.png'),
        ('textures/blocks/transformation_table_top.png', 'Transformation Table RP/textures/blocks/transformation_table_top.png')
    ]
    
    logger.info("Starting texture file processing...")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Files in current directory: {os.listdir('.')}")
    
    if os.path.exists('textures'):
        logger.info(f"Textures directory exists. Contents: {os.listdir('textures')}")
        if os.path.exists('textures/blocks'):
            logger.info(f"Textures/blocks directory contents: {os.listdir('textures/blocks')}")
        else:
            logger.warning("textures/blocks directory does not exist")
    else:
        logger.warning("textures directory does not exist")
    
    for local_path, zip_path in texture_files:
        try:
            logger.info(f"Processing texture: {local_path}")
            if os.path.exists(local_path):
                with open(local_path, 'rb') as texture_file:
                    texture_content = texture_file.read()
                zipf.writestr(zip_path, texture_content)
                logger.info(f"Successfully added real texture: {local_path} -> {zip_path} ({len(texture_content)} bytes)")
            else:
                # Fall back to placeholder if texture file doesn't exist
                placeholder_png = create_placeholder_texture()
                zipf.writestr(zip_path, placeholder_png)
                logger.warning(f"Texture not found at {local_path}, using placeholder")
        except Exception as e:
            logger.error(f"Error processing texture {local_path}: {e}")
            # Add placeholder on error
            try:
                placeholder_png = create_placeholder_texture()
                zipf.writestr(zip_path, placeholder_png)
                logger.info(f"Added placeholder for {zip_path} due to error")
            except Exception as e2:
                logger.error(f"Error creating placeholder for {zip_path}: {e2}")
    
    logger.info("Complete pack metadata added (BP + RP)")

def create_placeholder_texture():
    """Create a simple placeholder texture for the block faces"""
    # Minimal 16x16 PNG file (transparent placeholder)
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x1dIDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00\x18\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'

def add_custom_metadata(zipf, items):
    """Add README for custom structure"""
    try:
        readme_content = f"""# Custom Transformation Recipe Pack

This pack contains {len(items)-1} transformation recipes organized by category.

## Transformation Chain:
"""
        # Show the transformation chain
        for i in range(len(items) - 1):
            readme_content += f"{items[i]} → {items[i+1]}\n"
        
        readme_content += f"""
## Folder Structure:
- ores/ - Ore-related items
- metals/ - Ingots and metal items  
- wood/ - Wood and wooden items
- stone/ - Stone and rock items
- gems/ - Precious gems and crystals
- food/ - Food and consumable items
- misc/ - Everything else

## Installation:
Place the recipe files in your Minecraft data folder according to your needs.

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total items in chain: {len(items)}
"""
        zipf.writestr("README.md", readme_content)
        logger.info("Added custom metadata README")
    except Exception as e:
        logger.error(f"Error adding custom metadata: {e}")

@app.route("/download")
def download_zip():
    """Download the basic recipe ZIP"""
    try:
        if not os.path.exists(ZIP_PATH):
            logger.warning("ZIP file not found for download")
            return "ZIP file not found. Please generate recipes first.", 404
        
        # Check file size is reasonable
        file_size = os.path.getsize(ZIP_PATH)
        if file_size == 0:
            logger.error("ZIP file is empty")
            return "ZIP file is empty. Please regenerate recipes.", 404
        
        logger.info(f"Downloading ZIP file: {file_size:,} bytes")
        return send_file(ZIP_PATH, as_attachment=True, 
                        download_name="minecraft_transformation_recipes.zip", 
                        mimetype='application/zip')
    except Exception as e:
        logger.error(f"Error in download: {e}")
        return "Download failed. Please try again.", 500

@app.route("/api/last-session")
def get_last_session():
    """API endpoint to get last session data"""
    try:
        session_data = load_last_session()
        return jsonify(session_data)
    except Exception as e:
        logger.error(f"Error getting last session: {e}")
        return jsonify({"items": [], "selected": [], "timestamp": None})

@app.route("/api/update-session", methods=["POST"])
def update_session():
    """API endpoint to update session without generating recipes"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"})
        
        items = data.get("items", [])
        selected = data.get("selected", [])
        
        # Validate inputs
        items = validate_item_names(items)
        selected = validate_item_names(selected)
        
        # Save the session
        save_session(items, selected)
        
        return jsonify({"success": True, "message": "Session updated successfully"})
    except ValueError as e:
        logger.error(f"Validation error updating session: {e}")
        return jsonify({"success": False, "error": f"Invalid data: {str(e)}"})
    except Exception as e:
        logger.error(f"Error updating session: {e}")
        return jsonify({"success": False, "error": "Failed to save session"})

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template_string(HTML_TEMPLATE, 
                                message="", 
                                error="Page not found."), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return render_template_string(HTML_TEMPLATE, 
                                message="", 
                                error="Internal server error. Please try again."), 500

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Cleanup function for startup
def startup_cleanup():
    """Clean up old files on startup"""
    try:
        # Clean up old custom ZIP files
        if os.path.exists("data"):
            for filename in os.listdir("data"):
                if filename.startswith("custom_") and filename.endswith(".zip"):
                    file_path = os.path.join("data", filename)
                    try:
                        # Remove files older than 1 hour
                        if time.time() - os.path.getmtime(file_path) > 3600:
                            os.remove(file_path)
                            logger.info(f"Cleaned up old file: {filename}")
                    except Exception as e:
                        logger.warning(f"Could not clean up {filename}: {e}")
        
        # Clean up output directory
        cleanup_old_files()
        
    except Exception as e:
        logger.warning(f"Error in startup cleanup: {e}")

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("textures/blocks", exist_ok=True)
    
    # Perform startup cleanup
    startup_cleanup()
    
    # Log startup information
    logger.info("Starting Minecraft Recipe Generator")
    logger.info(f"Template path: {TEMPLATE_PATH}")
    logger.info(f"Pack icon path: {PACK_ICON_PATH}")
    logger.info(f"Texture directory: {TEXTURE_DIR}")
    logger.info(f"Debug templates: {DEBUG_TEMPLATES}")
    logger.info(f"Filtered items: {len(FILTERED_ITEMS)} items")
    
    # Check for required files
    if not os.path.exists(TEMPLATE_PATH):
        logger.error(f"Template file not found: {TEMPLATE_PATH}")
    else:
        logger.info(f"Template file found: {TEMPLATE_PATH}")
    
    if not os.path.exists(PACK_ICON_PATH):
        logger.warning(f"Pack icon not found: {PACK_ICON_PATH}")
    
    app.run(host="0.0.0.0", port=PORT, debug=False)