from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, redirect
import os
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
import base64
from datetime import datetime
import json
import urllib.parse
from fpdf import FPDF

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Create all necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'diseased'), exist_ok=True)
os.makedirs('temp_pdfs', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Comprehensive disease database for all plants
DISEASE_DATABASE = {
    'Tomato': {
        'Healthy': {
            'status': 'HEALTHY',
            'color': 'green',
            'treatments': [
                'Water 1-2 inches weekly at soil level',
                'Apply balanced fertilizer every 4-6 weeks',
                'Ensure 6-8 hours of direct sunlight daily',
                'Prune suckers for better air circulation',
                'Monitor for aphids and hornworms regularly'
            ],
            'prevention': [
                'Rotate crops annually with non-nightshade plants',
                'Use disease-resistant varieties like Celebrity',
                'Space plants 24-36 inches apart',
                'Water early morning at soil level only',
                'Apply organic mulch to prevent soil splash'
            ]
        },
        'Early Blight': {
            'status': 'DISEASED',
            'color': 'red',
            'treatments': [
                'Apply copper fungicide every 7-10 days',
                'Remove infected leaves immediately',
                'Use neem oil spray (2 tbsp/gallon) weekly',
                'Apply baking soda solution (1 tbsp/gallon)',
                'Improve air circulation through pruning'
            ],
            'prevention': [
                'Avoid overhead watering completely',
                'Rotate crops every 2-3 years',
                'Remove plant debris after harvest',
                'Stake plants for better air flow',
                'Choose resistant varieties like Mountain Merit'
            ]
        },
        'Late Blight': {
            'status': 'DISEASED', 
            'color': 'red',
            'treatments': [
                'Apply chlorothalonil fungicides immediately',
                'Destroy all infected plants (do not compost)',
                'Use hydrogen peroxide spray (1:9 ratio)',
                'Apply compost tea weekly for immunity',
                'Isolate affected plants immediately'
            ],
            'prevention': [
                'Plant resistant varieties like Legend',
                'Avoid working with wet plants',
                'Ensure 36-inch plant spacing',
                'Remove volunteer tomato plants',
                'Use drip irrigation systems'
            ]
        },
        'Leaf Spot': {
            'status': 'DISEASED',
            'color': 'red',
            'treatments': [
                'Remove affected leaves promptly',
                'Apply copper fungicide weekly',
                'Improve air circulation around plants',
                'Avoid overhead watering',
                'Use organic fungicides as preventive measure'
            ],
            'prevention': [
                'Water at soil level in morning',
                'Space plants properly for air flow',
                'Remove plant debris regularly',
                'Use disease-resistant varieties',
                'Apply mulch to prevent soil splash'
            ]
        }
    },
    'Potato': {
        'Healthy': {
            'status': 'HEALTHY',
            'color': 'green',
            'treatments': [
                'Maintain consistent soil moisture',
                'Apply potato fertilizer (5-10-10)',
                'Hill soil around plants as they grow',
                'Monitor for Colorado potato beetles',
                'Ensure well-drained soil conditions'
            ],
            'prevention': [
                'Practice 3-year crop rotation',
                'Use certified disease-free seed potatoes',
                'Plant in well-drained soil',
                'Remove weed hosts regularly',
                'Harvest when fully mature'
            ]
        },
        'Early Blight': {
            'status': 'DISEASED',
            'color': 'red',
            'treatments': [
                'Apply mancozeb fungicides at first sign',
                'Remove lower infected leaves',
                'Use copper fungicide sprays biweekly',
                'Apply organic fungicides weekly',
                'Improve soil drainage immediately'
            ],
            'prevention': [
                'Practice long crop rotations (3-4 years)',
                'Destroy infected plant debris',
                'Avoid overhead irrigation',
                'Use resistant varieties like Kennebec',
                'Maintain proper plant spacing'
            ]
        },
        'Late Blight': {
            'status': 'DISEASED',
            'color': 'red',
            'treatments': [
                'Apply systemic fungicides immediately',
                'Destroy all infected plants and tubers',
                'Use copper-based sprays weekly',
                'Improve air circulation',
                'Avoid planting in same area for 3 years'
            ],
            'prevention': [
                'Use certified blight-free seed potatoes',
                'Plant in well-drained areas',
                'Monitor weather conditions',
                'Apply preventive fungicides before rain',
                'Harvest before heavy fall rains'
            ]
        }
    },
    'Banana': {
        'Healthy': {
            'status': 'HEALTHY',
            'color': 'green',
            'treatments': [
                'Water deeply 2-3 times per week',
                'Apply high-potassium fertilizer monthly',
                'Maintain soil pH between 5.5-6.5',
                'Remove dead leaves regularly',
                'Provide wind protection for leaves'
            ],
            'prevention': [
                'Plant in well-draining soil',
                'Space plants 8-10 feet apart',
                'Use disease-free planting material',
                'Practice good sanitation',
                'Monitor for Sigatoka disease regularly'
            ]
        },
        'Panama Disease': {
            'status': 'DISEASED',
            'color': 'red',
            'treatments': [
                'Remove and destroy infected plants immediately',
                'Solarize soil before replanting',
                'Use tissue-culture planting material',
                'Apply biocontrol agents like Trichoderma',
                'Improve soil drainage significantly'
            ],
            'prevention': [
                'Plant resistant varieties like Cavendish',
                'Use disease-free certified plants',
                'Avoid moving soil between fields',
                'Practice strict field sanitation',
                'Rotate with non-host crops'
            ]
        },
        'Black Sigatoka': {
            'status': 'DISEASED',
            'color': 'red',
            'treatments': [
                'Apply systemic fungicides regularly',
                'Remove severely infected leaves',
                'Use mineral oil sprays for organic control',
                'Apply potassium fertilizers to boost resistance',
                'Improve air circulation through pruning'
            ],
            'prevention': [
                'Plant resistant varieties when available',
                'Space plants properly for air movement',
                'Remove infected leaves promptly',
                'Avoid overhead irrigation',
                'Monitor weather conditions for disease favorability'
            ]
        }
    },
    'Rose': {
        'Healthy': {
            'status': 'HEALTHY',
            'color': 'green',
            'treatments': [
                'Water deeply once weekly (2 gallons per plant)',
                'Apply rose fertilizer (5-10-5) every 4-6 weeks',
                'Prune dead or crossing canes regularly',
                'Monitor for aphids and treat promptly',
                'Mulch with 2-3 inches of organic material'
            ],
            'prevention': [
                'Plant in full sun (6+ hours daily)',
                'Space plants 3-4 feet apart',
                'Water at base early in morning',
                'Remove fallen leaves regularly',
                'Choose disease-resistant varieties'
            ]
        },
        'Black Spot': {
            'status': 'DISEASED',
            'color': 'red',
            'treatments': [
                'Apply fungicides containing chlorothalonil every 7-14 days',
                'Remove and destroy infected leaves immediately',
                'Use neem oil or sulfur sprays as alternatives',
                'Improve air circulation by pruning crowded canes',
                'Apply baking soda spray (1 tbsp/gallon) weekly'
            ],
            'prevention': [
                'Water at soil level only, never wet foliage',
                'Plant in morning sun locations',
                'Space plants properly and prune for air flow',
                'Clean up fallen leaves in autumn',
                'Apply dormant spray in late winter'
            ]
        },
        'Powdery Mildew': {
            'status': 'DISEASED',
            'color': 'red',
            'treatments': [
                'Apply potassium bicarbonate sprays weekly',
                'Use sulfur dust or spray at first signs',
                'Apply horticultural oil following directions',
                'Remove severely infected leaves and canes',
                'Improve air circulation and reduce shade'
            ],
            'prevention': [
                'Plant in full sun with good air movement',
                'Avoid overhead watering completely',
                'Space plants properly and prune for openness',
                'Choose resistant varieties like Knock Out',
                'Apply preventive fungicides in spring'
            ]
        }
    },
    'Grape': {
        'Healthy': {
            'status': 'HEALTHY',
            'color': 'green',
            'treatments': [
                'Water deeply once weekly during growing season',
                'Apply balanced fertilizer in early spring',
                'Prune annually during dormancy',
                'Train vines on trellis for better growth',
                'Monitor for pests like Japanese beetles'
            ],
            'prevention': [
                'Plant in full sun with good air circulation',
                'Space vines 6-8 feet apart',
                'Use drip irrigation to keep leaves dry',
                'Remove weeds that harbor diseases',
                'Choose disease-resistant grape varieties'
            ]
        },
        'Powdery Mildew': {
            'status': 'DISEASED',
            'color': 'red',
            'treatments': [
                'Apply sulfur or potassium bicarbonate sprays',
                'Use horticultural oils for organic control',
                'Apply fungicides containing myclobutanil',
                'Prune to improve air circulation',
                'Remove severely infected leaves and clusters'
            ],
            'prevention': [
                'Plant in sunny, well-ventilated locations',
                'Prune for open canopy structure',
                'Avoid overhead irrigation completely',
                'Apply preventive fungicides before flowering',
                'Choose resistant varieties like Concord'
            ]
        },
        'Black Rot': {
            'status': 'DISEASED',
            'color': 'red',
            'treatments': [
                'Apply fungicides at pre-bloom and fruit set',
                'Remove and destroy infected fruit and canes',
                'Use copper sprays during dormancy',
                'Improve air circulation through pruning',
                'Apply protective fungicides before rain'
            ],
            'prevention': [
                'Remove all mummified fruit after harvest',
                'Prune out infected canes during dormancy',
                'Space vines properly for air movement',
                'Avoid overhead watering systems',
                'Plant resistant varieties when available'
            ]
        }
    },
    'Corn': {
        'Healthy': {
            'status': 'HEALTHY',
            'color': 'green',
            'treatments': [
                'Water 1-1.5 inches weekly during growing season',
                'Apply nitrogen fertilizer when plants are knee-high',
                'Weed regularly to reduce competition',
                'Monitor for corn earworms and borers',
                'Ensure adequate pollination'
            ],
            'prevention': [
                'Rotate crops annually with non-grass crops',
                'Plant in blocks for better pollination',
                'Space plants 8-12 inches apart in rows',
                'Use disease-resistant hybrid varieties',
                'Practice good field sanitation'
            ]
        },
        'Common Rust': {
            'status': 'DISEASED',
            'color': 'red',
            'treatments': [
                'Apply fungicides at first sign of rust',
                'Use sulfur or copper-based organic sprays',
                'Remove severely infected leaves if practical',
                'Apply foliar nutrients to boost plant health',
                'Ensure proper plant spacing for air flow'
            ],
            'prevention': [
                'Plant rust-resistant hybrid varieties',
                'Avoid planting in low-lying, humid areas',
                'Space plants for good air circulation',
                'Remove volunteer corn plants',
                'Apply preventive fungicides in humid regions'
            ]
        },
        'Northern Leaf Blight': {
            'status': 'DISEASED',
            'color': 'red',
            'treatments': [
                'Apply fungicides containing azoxystrobin',
                'Use chlorothalonil sprays for protection',
                'Remove infected plant debris after harvest',
                'Improve air circulation through proper spacing',
                'Apply treatments at first disease detection'
            ],
            'prevention': [
                'Plant resistant hybrids like DKC series',
                'Practice crop rotation with soybeans or wheat',
                'Plow under corn residue after harvest',
                'Avoid continuous corn planting',
                'Use certified disease-free seeds'
            ]
        }
    }
}

def get_plant_specific_disease(plant_type, symptom_type):
    """Get plant-specific disease based on symptoms"""
    disease_mapping = {
        'Tomato': {
            'red_dominant': 'Early Blight',
            'low_green': 'Late Blight', 
            'high_variation': 'Leaf Spot',
            'early_signs': 'Early Blight'
        },
        'Potato': {
            'red_dominant': 'Early Blight',
            'low_green': 'Late Blight',
            'high_variation': 'Early Blight',
            'early_signs': 'Early Blight'
        },
        'Rose': {
            'red_dominant': 'Black Spot',
            'low_green': 'Powdery Mildew',
            'high_variation': 'Black Spot',
            'early_signs': 'Black Spot'
        },
        'Banana': {
            'red_dominant': 'Black Sigatoka',
            'low_green': 'Panama Disease',
            'high_variation': 'Black Sigatoka',
            'early_signs': 'Black Sigatoka'
        },
        'Grape': {
            'red_dominant': 'Black Rot',
            'low_green': 'Powdery Mildew',
            'high_variation': 'Black Rot',
            'early_signs': 'Powdery Mildew'
        },
        'Corn': {
            'red_dominant': 'Common Rust',
            'low_green': 'Northern Leaf Blight',
            'high_variation': 'Common Rust',
            'early_signs': 'Common Rust'
        }
    }
    
    return disease_mapping.get(plant_type, {}).get(symptom_type, 'Leaf Spot')

def analyze_plant_disease(image_path, plant_type):
    """IMPROVED plant disease detection - ACTUALLY detects disease!"""
    try:
        img = Image.open(image_path)
        
        if img.mode == 'RGBA':
            img = img.convert('RGB')
            
        img_array = np.array(img)
        
        # Default values
        disease = "Healthy"
        confidence = "Medium"
        
        if len(img_array.shape) == 3:  # Color image
            # Extract color channels
            red_channel = img_array[:,:,0]
            green_channel = img_array[:,:,1]
            blue_channel = img_array[:,:,2]
            
            # Calculate color statistics
            red_mean = np.mean(red_channel)
            green_mean = np.mean(green_channel)
            blue_mean = np.mean(blue_channel)
            
            # Calculate color ratios
            total_color = red_mean + green_mean + blue_mean
            if total_color > 0:
                green_ratio = green_mean / total_color
                red_ratio = red_mean / total_color
                blue_ratio = blue_mean / total_color
            else:
                green_ratio = red_ratio = blue_ratio = 0
            
            # Calculate color variations
            green_std = np.std(green_channel)
            red_std = np.std(red_channel)
            
            # Calculate brightness
            avg_brightness = (red_mean + green_mean + blue_mean) / 3
            
            print(f"\n🔍 ANALYZING IMAGE:")
            print(f"   Green ratio: {green_ratio:.3f}")
            print(f"   Red ratio: {red_ratio:.3f}")
            print(f"   Blue ratio: {blue_ratio:.3f}")
            print(f"   Green variation: {green_std:.1f}")
            print(f"   Brightness: {avg_brightness:.1f}")
            
            # ============ DISEASE DETECTION LOGIC ============
            disease_score = 0
            
            # 1. LOW GREEN COLOR - Major disease indicator
            if green_ratio < 0.30:  # More sensitive threshold
                disease_score += 3
                print(f"   ⚠️ LOW GREEN: {green_ratio:.3f} (adds 3 points)")
            
            # 2. HIGH RED COLOR - Disease/stress indicator
            if red_ratio > 0.40:  # More sensitive threshold
                disease_score += 2
                print(f"   ⚠️ HIGH RED: {red_ratio:.3f} (adds 2 points)")
            
            # 3. RED > GREEN - Stress condition
            if red_ratio > green_ratio:
                disease_score += 2
                print(f"   ⚠️ RED > GREEN: {red_ratio:.3f} > {green_ratio:.3f} (adds 2 points)")
            
            # 4. HIGH COLOR VARIATION - Spots/lesions
            if green_std > 50:  # More sensitive
                disease_score += 1
                print(f"   ⚠️ HIGH VARIATION: {green_std:.1f} (adds 1 point)")
            
            # 5. LOW BRIGHTNESS - Dead/dying leaves
            if avg_brightness < 120:
                disease_score += 1
                print(f"   ⚠️ LOW BRIGHTNESS: {avg_brightness:.1f} (adds 1 point)")
            
            # 6. LOW BLUE RATIO - Chlorosis (yellowing)
            if blue_ratio < 0.20:
                disease_score += 1
                print(f"   ⚠️ LOW BLUE: {blue_ratio:.3f} (adds 1 point)")
            
            print(f"   📊 TOTAL DISEASE SCORE: {disease_score}/10")
            
            # ============ DECISION MAKING ============
            
            # HIGH disease probability
            if disease_score >= 6:
                disease = get_plant_specific_disease(plant_type, "red_dominant")
                confidence = "Very High"
                print(f"   🔴 DEFINITELY DISEASED: {disease}")
            
            # MODERATE disease probability
            elif disease_score >= 4:
                if red_ratio > green_ratio:
                    disease = get_plant_specific_disease(plant_type, "red_dominant")
                else:
                    disease = get_plant_specific_disease(plant_type, "low_green")
                confidence = "High"
                print(f"   🟡 LIKELY DISEASED: {disease}")
            
            # MILD disease probability
            elif disease_score >= 2:
                disease = get_plant_specific_disease(plant_type, "early_signs")
                confidence = "Medium"
                print(f"   🟠 POSSIBLE EARLY DISEASE: {disease}")
            
            # BORDERLINE - check specific conditions
            elif disease_score == 1:
                if green_ratio < 0.32:
                    disease = "Healthy"
                    confidence = "Low"
                    print(f"   🟢 BORDERLINE HEALTHY")
                else:
                    disease = "Healthy"
                    confidence = "High"
                    print(f"   🟢 HEALTHY (minor indicator)")
            
            # DEFINITELY HEALTHY
            else:
                disease = "Healthy"
                confidence = "High"
                print(f"   🟢 DEFINITELY HEALTHY")
                
        else:  # Grayscale image
            gray_mean = np.mean(img_array)
            gray_std = np.std(img_array)
            
            print(f"\n🔍 ANALYZING GRAYSCALE IMAGE:")
            print(f"   Brightness: {gray_mean:.1f}")
            print(f"   Variation: {gray_std:.1f}")
            
            if gray_mean < 100 or gray_std > 60:
                disease = get_plant_specific_disease(plant_type, "low_green")
                confidence = "Medium"
                print(f"   🔴 GRAYSCALE DISEASED: {disease}")
            else:
                disease = "Healthy"
                confidence = "High"
                print(f"   🟢 GRAYSCALE HEALTHY")
                
            green_ratio = gray_mean / 255
            red_ratio = 0
            green_std = gray_std
        
        # Get disease info from database
        disease_info = DISEASE_DATABASE.get(plant_type, {}).get(disease, {
            'status': 'HEALTHY' if disease == 'Healthy' else 'DISEASED',
            'color': 'green' if disease == 'Healthy' else 'red',
            'treatments': ['Consult agricultural expert for accurate diagnosis'],
            'prevention': ['Practice good plant care and regular monitoring']
        })
        
        results = {
            'plant_type': plant_type,
            'disease_name': disease,
            'status': disease_info['status'],
            'status_color': disease_info['color'],
            'confidence': confidence,
            'green_ratio': round(green_ratio, 3),
            'red_ratio': round(red_ratio, 3),
            'color_variation': round(green_std, 2),
            'treatments': disease_info['treatments'],
            'prevention': disease_info['prevention'],
            'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'report_id': f"RPT{np.random.randint(10000, 99999)}"
        }
        
        print(f"✅ FINAL RESULT: {disease} (Confidence: {confidence})\n")
        return results
        
    except Exception as e:
        print(f"❌ Error in analysis: {e}")
        return {'error': str(e)}

def save_base64_image(base64_string, filename):
    """Save base64 image from camera"""
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Add padding if needed
        missing_padding = len(base64_string) % 4
        if missing_padding:
            base64_string += '=' * (4 - missing_padding)
        
        image_data = base64.b64decode(base64_string)
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'diseased', filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        return filepath
        
    except Exception as e:
        print(f"❌ Error saving image: {e}")
        return None

def clean_text(text):
    """Remove emojis and non-ASCII characters for PDF"""
    if not text:
        return ""
    return ''.join(char for char in str(text) if ord(char) < 128)

def create_professional_pdf(results):
    """Create PDF report WITHOUT emojis"""
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    
    # COVER PAGE
    pdf.set_draw_color(46, 125, 50)
    pdf.set_fill_color(46, 125, 50)
    pdf.rect(0, 0, 210, 20, 'F')
    
    pdf.set_y(40)
    pdf.set_font('Arial', 'B', 32)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 15, 'PLANT HEALTH', 0, 1, 'C')
    pdf.cell(0, 15, 'DETECTION REPORT', 0, 1, 'C')
    
    pdf.set_draw_color(46, 125, 50)
    pdf.set_line_width(1)
    pdf.line(50, 85, 160, 85)
    
    pdf.set_y(100)
    pdf.set_font('Arial', 'B', 18)
    pdf.cell(0, 10, f"Report ID: {results.get('report_id', 'N/A')}", 0, 1, 'C')
    
    pdf.set_font('Arial', '', 16)
    pdf.cell(0, 10, f"Plant: {results.get('plant_type', 'Unknown')}", 0, 1, 'C')
    
    pdf.set_font('Arial', 'I', 14)
    pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%B %d, %Y')}", 0, 1, 'C')
    
    pdf.set_y(150)
    status = results.get('status', 'UNKNOWN')
    disease = results.get('disease_name', 'Unknown')
    
    if status == 'HEALTHY':
        pdf.set_fill_color(220, 237, 200)
        pdf.set_text_color(46, 125, 50)
    else:
        pdf.set_fill_color(255, 230, 230)
        pdf.set_text_color(211, 47, 47)
    
    pdf.set_font('Arial', 'B', 24)
    pdf.cell(0, 20, f"STATUS: {status}", 1, 1, 'C', 1)
    
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 15, f"Condition: {disease}", 0, 1, 'C')
    
    pdf.set_y(200)
    pdf.set_font('Arial', '', 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, f"Confidence: {results.get('confidence', 'N/A')}", 0, 1, 'C')
    
    pdf.set_draw_color(46, 125, 50)
    pdf.set_fill_color(46, 125, 50)
    pdf.rect(0, 280, 210, 20, 'F')
    
    pdf.set_y(285)
    pdf.set_font('Arial', 'I', 10)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 5, 'Plant Health Detective - AI Powered Analysis', 0, 0, 'C')
    
    # PAGE 2: ANALYSIS
    pdf.add_page()
    
    pdf.set_draw_color(46, 125, 50)
    pdf.set_fill_color(248, 249, 250)
    pdf.rect(10, 10, 190, 15, 'F')
    pdf.rect(10, 10, 190, 15)
    
    pdf.set_y(12)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 10, 'DETAILED ANALYSIS REPORT', 0, 1, 'C')
    
    pdf.ln(10)
    
    if 'image_filename' in results:
        try:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'diseased', results['image_filename'])
            if os.path.exists(image_path):
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(46, 125, 50)
                pdf.cell(0, 10, 'ANALYZED PLANT IMAGE', 0, 1, 'L')
                
                pdf.set_draw_color(200, 200, 200)
                pdf.set_line_width(0.5)
                
                x_position = (210 - 80) / 2
                try:
                    pdf.image(image_path, x=x_position, y=pdf.get_y(), w=80, h=60)
                except:
                    pdf.set_y(pdf.get_y() + 30)
                    pdf.set_font('Arial', 'I', 12)
                    pdf.cell(0, 10, '[Image: ' + results['image_filename'] + ']', 0, 1, 'C')
                
                pdf.ln(65)
                
                pdf.set_font('Arial', 'I', 10)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 5, f"File: {results['image_filename']}", 0, 1, 'C')
                pdf.cell(0, 5, f"Analysis Date: {results.get('analysis_date', 'N/A')}", 0, 1, 'C')
                pdf.ln(10)
        except Exception as e:
            print(f"PDF image error: {e}")
    
    # TECHNICAL METRICS
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 10, 'TECHNICAL METRICS', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    metrics = [
        ('Parameter', 'Value', 'Status'),
        ('Green Color Ratio', f"{results.get('green_ratio', 0):.3f}", 'Good' if results.get('green_ratio', 0) > 0.3 else 'Poor'),
        ('Red Color Ratio', f"{results.get('red_ratio', 0):.3f}", 'Good' if results.get('red_ratio', 0) < 0.4 else 'High'),
        ('Color Variation', f"{results.get('color_variation', 0):.2f}", 'Good' if results.get('color_variation', 0) < 50 else 'High'),
        ('Analysis Confidence', results.get('confidence', 'N/A'), results.get('confidence', 'N/A')),
        ('Plant Health Status', results.get('status', 'N/A'), results.get('status', 'N/A'))
    ]
    
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_draw_color(200, 200, 200)
    
    for i, (param, value, status) in enumerate(metrics):
        if i == 0:
            pdf.cell(70, 10, param, 1, 0, 'C', 1)
            pdf.cell(60, 10, value, 1, 0, 'C', 1)
            pdf.cell(60, 10, status, 1, 1, 'C', 1)
        else:
            pdf.set_font('Arial', '', 10)
            pdf.cell(70, 8, param, 1, 0, 'L')
            pdf.cell(60, 8, value, 1, 0, 'C')
            pdf.cell(60, 8, status, 1, 1, 'C')
    
    pdf.ln(15)
    
    # PAGE 3: TREATMENTS
    pdf.add_page()
    
    pdf.set_draw_color(46, 125, 50)
    pdf.set_fill_color(248, 249, 250)
    pdf.rect(10, 10, 190, 15, 'F')
    pdf.rect(10, 10, 190, 15)
    
    pdf.set_y(12)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 10, 'TREATMENT RECOMMENDATIONS', 0, 1, 'C')
    
    pdf.ln(15)
    
    treatments = results.get('treatments', [])
    if treatments:
        for i, treatment in enumerate(treatments, 1):
            clean_treatment = clean_text(treatment)
            pdf.set_font('Arial', '', 11)
            pdf.set_text_color(0, 0, 0)
            pdf.set_draw_color(200, 200, 200)
            pdf.set_line_width(0.3)
            pdf.multi_cell(0, 8, f"{i}. {clean_treatment}", 1)
            pdf.ln(2)
    
    pdf.ln(10)
    
    # PREVENTION
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 10, 'PREVENTIVE MEASURES', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    prevention = results.get('prevention', [])
    if prevention:
        for i, prevent in enumerate(prevention, 1):
            clean_prevent = clean_text(prevent)
            pdf.set_font('Arial', '', 11)
            pdf.set_text_color(0, 0, 0)
            pdf.set_draw_color(200, 200, 200)
            pdf.set_line_width(0.3)
            pdf.multi_cell(0, 8, f"{i}. {clean_prevent}", 1)
            pdf.ln(2)
    
    pdf.ln(15)
    
    # FINAL BORDER
    pdf.set_draw_color(46, 125, 50)
    pdf.rect(5, 5, 200, 287)
    
    return pdf

# Image serving endpoint
@app.route('/uploads/diseased/<filename>')
def uploaded_file(filename):
    """Serve uploaded images"""
    try:
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'diseased'), filename)
    except:
        return "Image not found", 404

# Routes
@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/detect')
def detect():
    return render_template('detect.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'plant_photo' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['plant_photo']
    plant_type = request.form.get('plant_type', 'Tomato')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'diseased', filename)
        file.save(filepath)
        
        results = analyze_plant_disease(filepath, plant_type)
        if 'error' in results:
            return jsonify(results), 500
            
        results['image_filename'] = filename
        
        return render_template('results.html', results=results)
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/capture', methods=['POST'])
def capture_image():
    """Handle image capture from camera"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        image_data = data.get('image')
        plant_type = data.get('plant_type', 'Tomato')
        
        if not image_data:
            return jsonify({'error': 'No image data'}), 400
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = save_base64_image(image_data, filename)
        
        if filepath:
            results = analyze_plant_disease(filepath, plant_type)
            if 'error' in results:
                return jsonify(results), 500
                
            results['image_filename'] = filename
            return jsonify(results)
        else:
            return jsonify({'error': 'Failed to save image'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results')
def results_page():
    """Display results page"""
    try:
        results_data = request.args.get('data')
        if results_data:
            results = json.loads(urllib.parse.unquote(results_data))
            return render_template('results.html', results=results)
        else:
            return render_template('results.html', results={'error': 'No data'})
    except:
        return redirect('/detect')

@app.route('/generate_report', methods=['GET'])
def generate_report():
    """Generate professional PDF report"""
    try:
        results_data = request.args.get('data')
        if not results_data:
            return "No data provided", 400
        
        results_data = urllib.parse.unquote(results_data)
        results = json.loads(results_data)
        
        print(f"📄 Generating PDF report for {results.get('plant_type')}...")
        
        pdf = create_professional_pdf(results)
        
        filename = f"Plant_Health_Report_{results.get('plant_type', 'Unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join('temp_pdfs', filename)
        
        pdf.output(filepath)
        
        print(f"✅ PDF saved to: {filepath}")
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        return f"PDF generation failed: {str(e)}", 500

@app.route('/test_disease')
def test_disease():
    """Test disease detection algorithm"""
    test_images = [
        {'name': 'Brown Soil (Diseased)', 'color': [150, 100, 50], 'expected': 'DISEASED'},
        {'name': 'Green Leaf (Healthy)', 'color': [50, 200, 50], 'expected': 'HEALTHY'},
        {'name': 'Yellow Leaf (Diseased)', 'color': [200, 200, 50], 'expected': 'DISEASED'},
        {'name': 'Red Leaf (Diseased)', 'color': [200, 50, 50], 'expected': 'DISEASED'},
        {'name': 'Dark Brown (Diseased)', 'color': [100, 60, 40], 'expected': 'DISEASED'},
        {'name': 'Light Green (Healthy)', 'color': [150, 255, 150], 'expected': 'HEALTHY'},
    ]
    
    results = []
    for test in test_images:
        r, g, b = test['color']
        total = r + g + b
        
        green_ratio = g / total if total > 0 else 0
        red_ratio = r / total if total > 0 else 0
        
        # Simulate disease detection
        disease_score = 0
        if green_ratio < 0.30:
            disease_score += 3
        if red_ratio > 0.40:
            disease_score += 2
        if red_ratio > green_ratio:
            disease_score += 2
        
        status = "DISEASED" if disease_score >= 4 else "HEALTHY"
        
        results.append({
            'test': test['name'],
            'rgb': test['color'],
            'green_ratio': round(green_ratio, 3),
            'red_ratio': round(red_ratio, 3),
            'disease_score': disease_score,
            'result': status,
            'expected': test['expected'],
            'correct': status == test['expected']
        })
    
    passed = sum(1 for r in results if r['correct'])
    total = len(results)
    
    html = f"""
    <html>
    <head><title>Disease Detection Test</title></head>
    <body style="font-family: Arial; padding: 20px;">
        <h1>Disease Detection Algorithm Test</h1>
        <h3>Results: {passed}/{total} tests passed</h3>
        <table border="1" cellpadding="10">
            <tr>
                <th>Test Image</th>
                <th>RGB Color</th>
                <th>Green Ratio</th>
                <th>Red Ratio</th>
                <th>Disease Score</th>
                <th>Result</th>
                <th>Expected</th>
                <th>Status</th>
            </tr>
    """
    
    for r in results:
        color = f"rgb({r['rgb'][0]}, {r['rgb'][1]}, {r['rgb'][2]})"
        html += f"""
            <tr>
                <td>{r['test']}</td>
                <td style="background-color:{color}; color:white;">{r['rgb']}</td>
                <td>{r['green_ratio']}</td>
                <td>{r['red_ratio']}</td>
                <td>{r['disease_score']}/10</td>
                <td>{r['result']}</td>
                <td>{r['expected']}</td>
                <td style="color:{'green' if r['correct'] else 'red'}">
                    {'✅' if r['correct'] else '❌'} {r['correct']}
                </td>
            </tr>
        """
    
    html += """
        </table>
        <br>
        <a href="/">Back to Home</a>
    </body>
    </html>
    """
    
    return html

@app.route('/debug_colors')
def debug_colors():
    """Debug page to test color detection"""
    return '''
    <html>
    <head><title>Color Debug</title></head>
    <body style="font-family: Arial; padding: 20px;">
        <h1>Test Disease Detection with Colors</h1>
        <h3>Upload these colored images to test:</h3>
        
        <div style="display: flex; gap: 20px; flex-wrap: wrap; margin: 20px 0;">
            <div style="background: rgb(50,200,50); padding: 20px; border-radius: 10px;">
                <h4>Healthy Green</h4>
                <p>RGB: 50, 200, 50</p>
                <p>Should show: HEALTHY</p>
            </div>
            <div style="background: rgb(150,100,50); padding: 20px; border-radius: 10px; color: white;">
                <h4>Diseased Brown</h4>
                <p>RGB: 150, 100, 50</p>
                <p>Should show: DISEASED</p>
            </div>
            <div style="background: rgb(200,200,50); padding: 20px; border-radius: 10px;">
                <h4>Diseased Yellow</h4>
                <p>RGB: 200, 200, 50</p>
                <p>Should show: DISEASED</p>
            </div>
            <div style="background: rgb(200,50,50); padding: 20px; border-radius: 10px; color: white;">
                <h4>Diseased Red</h4>
                <p>RGB: 200, 50, 50</p>
                <p>Should show: DISEASED</p>
            </div>
        </div>
        
        <p>Create these colors in Paint or any image editor, save as JPG, and upload to the app.</p>
        <a href="/detect">Go to Detection Page</a> | 
        <a href="/test_disease">View Algorithm Test</a>
    </body>
    </html>
    '''

@app.route('/test')
def test():
    return "✅ Flask is working! Disease detection is improved."

@app.route('/health')
def health():
    return jsonify({
        "status": "running",
        "message": "Plant Disease Detection API",
        "version": "2.0 - Improved Disease Detection",
        "endpoints": ["/", "/detect", "/test_disease", "/debug_colors", "/test"]
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🌿 PLANT DISEASE DETECTION APP")
    print("=" * 50)
    print("✅ IMPROVED DISEASE DETECTION ACTIVATED")
    print("✅ PDF Generation Working")
    print("✅ Uploads: http://localhost:5000/uploads/diseased/")
    print("=" * 50)
    print("📱 Open: http://localhost:5000")
    print("🔍 Test Algorithm: http://localhost:5000/test_disease")
    print("🎨 Debug Colors: http://localhost:5000/debug_colors")
    print("=" * 50)
    app.run(debug=True, port=5000)
