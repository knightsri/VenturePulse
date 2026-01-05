#!/usr/bin/env python3
"""
VenturePulse Index Generator
Creates an attractive index.html for multi-model analysis comparisons.

Usage:
    python3 createindex.py <directory>
    python3 createindex.py .
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

def calculate_duration_from_files(folder):
    """Calculate analysis duration from file creation timestamps."""
    try:
        html_files = list(folder.glob('section*.html'))
        if not html_files:
            return None
        
        # Get creation times
        timestamps = [f.stat().st_mtime for f in html_files]
        
        if len(timestamps) < 2:
            return None
        
        # Calculate duration in minutes
        duration_seconds = max(timestamps) - min(timestamps)
        duration_minutes = int(duration_seconds / 60)
        
        if duration_minutes < 1:
            return "< 1 min"
        elif duration_minutes < 60:
            return f"{duration_minutes} min"
        else:
            hours = duration_minutes // 60
            mins = duration_minutes % 60
            return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
    except Exception as e:
        print(f"Warning: Could not calculate duration for {folder}: {e}")
        return None

def parse_provenance_html(provenance_file):
    """Parse provenance HTML to extract model info and metadata."""
    try:
        with open(provenance_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract model name
        model_match = re.search(r'<strong>Model:</strong>\s*([^<]+)', content)
        model = model_match.group(1).strip() if model_match else None
        
        # Extract provider
        provider_match = re.search(r'<strong>Provider:</strong>\s*([^<]+)', content)
        provider = provider_match.group(1).strip() if provider_match else None
        
        # Extract generation date
        date_match = re.search(r'<strong>Generated:</strong>\s*([^<]+)', content)
        generated = date_match.group(1).strip() if date_match else None
        
        return {
            'model': model,
            'provider': provider,
            'generated': generated,
        }
    except Exception as e:
        print(f"Warning: Could not parse provenance file {provenance_file}: {e}")
        return {}

def parse_model_name(folder_name):
    """Extract model name from folder name."""
    # Remove timestamp pattern (YYYYMMDD or YYYY-MM-DD or YYYYMMDD-HHMMSS)
    cleaned = re.sub(r'-\d{8}(-\d{6})?$', '', folder_name)
    cleaned = re.sub(r'-\d{4}-\d{2}-\d{2}.*$', '', cleaned)
    
    # Remove common prefixes/suffixes
    cleaned = re.sub(r'^.*?-analysis-', '', cleaned)
    
    # Model name mappings for display
    model_display_names = {
        'claude-sonnet-4-5': 'Claude Sonnet 4.5',
        'claude-sonnet-4': 'Claude Sonnet 4',
        'gemini-2-5-flash': 'Gemini 2.5 Flash',
        'gemini-2-5-pro': 'Gemini 2.5 Pro',
        'gemini-2-0-flash': 'Gemini 2.0 Flash',
        'gpt-4o': 'GPT-4o',
        'gpt-4o-mini': 'GPT-4o Mini',
        'gpt-5': 'GPT-5',
        'deepseek-r1': 'DeepSeek R1',
        'deepseek-r1t2-chimera-free': 'DeepSeek R1 Chimera',
        'deepseek-r1t2-chimera': 'DeepSeek R1 Chimera',
    }
    
    # Try to find a matching display name (check longer names first)
    for key in sorted(model_display_names.keys(), key=len, reverse=True):
        if key in cleaned:
            return model_display_names[key]
    
    # Fallback: capitalize and clean up
    return cleaned.replace('-', ' ').title()

def get_model_category(model_name):
    """Determine model category based on model name."""
    if not model_name:
        return 'standard'
    
    model_lower = model_name.lower()
    
    if 'claude' in model_lower and 'sonnet' in model_lower:
        return 'premium'
    elif 'gpt-5' in model_lower or 'gemini-2-5-pro' in model_lower:
        return 'premium'
    elif 'flash' in model_lower or 'mini' in model_lower:
        return 'fast'
    elif 'deepseek' in model_lower:
        return 'budget'
    else:
        return 'standard'

def read_project_description(md_file):
    """Extract project title and first few lines from markdown."""
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            # Get title (first heading or filename)
            title = Path(md_file).stem.replace('-', ' ').replace('_', ' ').title()
            for line in lines:
                if line.startswith('# '):
                    title = line.replace('# ', '').strip()
                    break
            
            # Get description (first paragraph after title)
            description = ''
            found_content = False
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    if found_content:
                        break
                    continue
                if line and not line.startswith('#'):
                    description += line + ' '
                    found_content = True
                    if len(description) > 300:
                        break
            
            return title, description[:300] + '...' if len(description) > 300 else description
    except Exception as e:
        print(f"Warning: Could not read {md_file}: {e}")
        return "Project Analysis", "Multi-model analysis comparison"

def generate_html(project_name, project_desc, analyses, timestamp):
    """Generate the complete HTML index page."""
    
    # Build model cards HTML
    model_cards = ''
    for analysis in analyses:
        provenance = analysis.get('provenance', {})
        
        model_name = provenance.get('model') or analysis['model']
        provider = provenance.get('provider')
        duration = analysis.get('duration', 'N/A')
        
        category = get_model_category(model_name)
        
        category_label = {
            'premium': 'Premium',
            'fast': 'Fast',
            'budget': 'Budget',
            'standard': 'Standard'
        }.get(category, 'Standard')
        
        category_color = {
            'premium': '#667eea',
            'fast': '#28a745',
            'budget': '#6c757d',
            'standard': '#17a2b8'
        }.get(category, '#17a2b8')
        
        # Only show provider if available
        provider_html = f'<p class="provider">{provider}</p>' if provider else ''
        
        model_cards += f'''
                <div class="model-card">
                    <span class="badge" style="background: {category_color};">{category_label}</span>
                    <h3>{model_name}</h3>
                    {provider_html}
                    
                    <div class="model-stats">
                        <div class="stat">
                            <span class="stat-value">{duration}</span>
                            <span class="stat-label">Duration</span>
                        </div>
                        <div class="stat">
                            <span class="stat-value">9</span>
                            <span class="stat-label">Reports</span>
                        </div>
                    </div>

                    <button onclick="openModal('{analysis['folder']}/index.html')" class="view-analysis-btn">
                        View Analysis →
                    </button>
                </div>
'''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - VenturePulse Analysis</title>
    <meta name="description" content="Multi-model AI analysis comparison for {project_name}">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem 1rem;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
        }}

        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
        }}

        header .subtitle {{
            font-size: 1.2rem;
            opacity: 0.95;
            font-weight: 300;
        }}

        .intro {{
            padding: 2rem;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}

        .intro h2 {{
            color: #667eea;
            margin-bottom: 1rem;
            font-size: 1.8rem;
        }}

        .intro p {{
            font-size: 1.05rem;
            margin-bottom: 1rem;
            color: #555;
            line-height: 1.8;
        }}

        .project-meta {{
            display: flex;
            gap: 2rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: #666;
            font-size: 0.95rem;
        }}

        .meta-item strong {{
            color: #667eea;
        }}

        .models-section {{
            padding: 2rem;
        }}

        .models-section h2 {{
            color: #333;
            margin-bottom: 1rem;
            font-size: 2rem;
            text-align: center;
        }}

        .models-intro {{
            text-align: center;
            margin-bottom: 2rem;
            color: #666;
            font-size: 1.1rem;
        }}

        .model-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }}

        .model-card {{
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 1.5rem;
            transition: all 0.3s ease;
            position: relative;
        }}

        .model-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            border-color: #667eea;
        }}

        .model-card .badge {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            color: white;
        }}

        .model-card h3 {{
            color: #333;
            margin-bottom: 0.5rem;
            font-size: 1.4rem;
            padding-right: 100px;
        }}

        .model-card .provider {{
            color: #6c757d;
            font-size: 0.85rem;
            margin-bottom: 1rem;
            font-family: 'Courier New', monospace;
        }}

        .model-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
            margin: 1.5rem 0;
        }}

        .stat {{
            text-align: center;
            padding: 0.75rem;
            background: #f8f9fa;
            border-radius: 6px;
        }}

        .stat-value {{
            display: block;
            font-size: 1.2rem;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 0.25rem;
        }}

        .stat-label {{
            font-size: 0.75rem;
            color: #6c757d;
            text-transform: uppercase;
        }}

        .view-analysis-btn {{
            display: block;
            width: 100%;
            padding: 0.75rem;
            background: #667eea;
            color: white;
            text-decoration: none;
            border: none;
            border-radius: 6px;
            text-align: center;
            font-weight: 600;
            transition: all 0.3s ease;
            margin-top: 1rem;
            cursor: pointer;
            font-size: 1rem;
        }}

        .view-analysis-btn:hover {{
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}

        /* Modal styles */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            animation: fadeIn 0.3s ease;
        }}

        .modal.active {{
            display: block;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        .modal-content {{
            position: relative;
            margin: 2% auto;
            width: 95%;
            height: 90%;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            overflow: hidden;
            animation: slideIn 0.3s ease;
        }}

        @keyframes slideIn {{
            from {{
                transform: translateY(-50px);
                opacity: 0;
            }}
            to {{
                transform: translateY(0);
                opacity: 1;
            }}
        }}

        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        .modal-header h3 {{
            margin: 0;
            font-size: 1.2rem;
        }}

        .close-btn {{
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }}

        .close-btn:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: rotate(90deg);
        }}

        .modal-body {{
            width: 100%;
            height: calc(100% - 60px);
            border: none;
        }}

        footer {{
            padding: 2rem;
            text-align: center;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
        }}

        footer a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }}

        footer a:hover {{
            text-decoration: underline;
        }}

        .watermark {{
            margin-top: 1rem;
            font-size: 0.85rem;
            opacity: 0.7;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 1rem 0.5rem;
            }}

            header h1 {{
                font-size: 1.8rem;
            }}

            .model-grid {{
                grid-template-columns: 1fr;
            }}

            .project-meta {{
                flex-direction: column;
                gap: 0.5rem;
            }}

            .modal-content {{
                width: 98%;
                height: 95%;
                margin: 1% auto;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎯 {project_name}</h1>
            <p class="subtitle">Multi-Model AI Analysis Comparison</p>
        </header>

        <section class="intro">
            <h2>About This Analysis</h2>
            <p>{project_desc}</p>
            
            <div class="project-meta">
                <div class="meta-item">
                    <strong>Models Analyzed:</strong> {len(analyses)}
                </div>
                <div class="meta-item">
                    <strong>Generated:</strong> {timestamp}
                </div>
                <div class="meta-item">
                    <strong>Tool:</strong> VenturePulse
                </div>
            </div>
        </section>

        <section class="models-section">
            <h2>🤖 Compare AI Model Analyses</h2>
            <p class="models-intro">
                Each model brings different strengths to the analysis. Click to explore how different AI models 
                approach market analysis, competitive positioning, technical feasibility, and strategic recommendations.
            </p>

            <div class="model-grid">
{model_cards}
            </div>
        </section>

        <footer>
            <p>
                Generated with <strong>VenturePulse</strong> • 
                <a href="https://github.com/knightsri/VenturePulse" target="_blank">GitHub</a> • 
                <a href="https://shalusri.com" target="_blank">Blog</a>
            </p>
            <p class="watermark">
                Open source, MIT licensed • AI-powered product viability analysis
            </p>
        </footer>
    </div>

    <!-- Modal -->
    <div id="analysisModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Analysis Report</h3>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <iframe id="modalFrame" class="modal-body"></iframe>
        </div>
    </div>

    <script>
        function openModal(url) {{
            const modal = document.getElementById('analysisModal');
            const frame = document.getElementById('modalFrame');
            frame.src = url;
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        function closeModal() {{
            const modal = document.getElementById('analysisModal');
            const frame = document.getElementById('modalFrame');
            modal.classList.remove('active');
            frame.src = '';
            document.body.style.overflow = 'auto';
        }}

        // Close modal on Escape key
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') {{
                closeModal();
            }}
        }});

        // Close modal when clicking outside
        document.getElementById('analysisModal').addEventListener('click', function(e) {{
            if (e.target === this) {{
                closeModal();
            }}
        }});
    </script>
</body>
</html>'''
    
    return html

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 createindex.py <directory>")
        print("Example: python3 createindex.py .")
        sys.exit(1)
    
    target_dir = Path(sys.argv[1]).resolve()
    
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"Error: {target_dir} is not a valid directory")
        sys.exit(1)
    
    print(f"Scanning directory: {target_dir}")
    
    # Find markdown file (project description)
    md_files = list(target_dir.glob('*.md'))
    if not md_files:
        print("Warning: No .md file found, using default project info")
        project_name = target_dir.name.replace('-', ' ').replace('_', ' ').title()
        project_desc = "Multi-model analysis comparison"
    else:
        md_file = md_files[0]
        print(f"Found project description: {md_file.name}")
        project_name, project_desc = read_project_description(md_file)
    
    # Find analysis directories (containing index.html)
    analyses = []
    for item in target_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            index_file = item / 'index.html'
            provenance_file = item / 'section09-provenance.html'
            
            if index_file.exists():
                model_name = parse_model_name(item.name)
                
                # Parse provenance if available
                provenance = {}
                if provenance_file.exists():
                    provenance = parse_provenance_html(provenance_file)
                    if provenance.get('model'):
                        model_name = provenance['model']
                
                # Calculate duration from file timestamps
                duration = calculate_duration_from_files(item)
                
                print(f"  Found analysis: {model_name} ({item.name})")
                if duration:
                    print(f"    Duration: {duration}")
                
                analyses.append({
                    'folder': item.name,
                    'model': model_name,
                    'provenance': provenance,
                    'duration': duration or 'N/A'
                })
    
    if not analyses:
        print("Error: No analysis directories with index.html found")
        sys.exit(1)
    
    # Sort analyses by model name
    analyses.sort(key=lambda x: x['model'])
    
    print(f"\nGenerating index.html for {len(analyses)} analyses...")
    
    # Generate HTML
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    html_content = generate_html(project_name, project_desc, analyses, timestamp)
    
    # Write to file
    output_file = target_dir / 'index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Successfully created: {output_file}")
    print(f"\nOpen in browser:")
    print(f"  file://{output_file}")

if __name__ == '__main__':
    main()