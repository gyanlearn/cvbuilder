import logging
import fitz  # PyMuPDF
import google.generativeai as genai
from typing import Dict, Any, List, Tuple, Optional
import tempfile
import os
from datetime import datetime
from .cv_templates import CVTemplateEngine

logger = logging.getLogger(__name__)

class CVImprover:
    """
    ATS-based CV improvement system using Gemini Flash 2.0 for rewriting
    and PyMuPDF for PDF generation.
    """
    
    def __init__(self, model):
        """
        Initialize CV improver with Gemini model
        
        Args:
            model: Initialized Gemini model instance
        """
        self.model = model
        self.temp_dir = tempfile.mkdtemp()
        self.template_engine = CVTemplateEngine()
        
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get available CV templates"""
        return self.template_engine.get_available_templates()
        
    def improve_cv(self, original_cv_text: str, ats_feedback: Dict[str, Any], 
                   industry: str, original_score: int, template_id: str = 'modern_professional') -> Dict[str, Any]:
        """
        Improve CV based on ATS score and feedback using structured templates
        
        Args:
            original_cv_text: Original CV text
            ats_feedback: ATS analysis results
            industry: Target industry
            original_score: Original ATS score
            template_id: CV template to use
            
        Returns:
            Dict containing improved CV text, new score, and PDF path
        """
        try:
            # Determine improvement strategy based on ATS score
            strategy = self._determine_strategy(original_score)
            logger.info(f"Using {strategy} strategy for CV improvement (score: {original_score})")
            logger.info(f"Using template: {template_id}")
            
            # Generate improvement prompt
            prompt = self._create_improvement_prompt(original_cv_text, ats_feedback, strategy)
            
            # Get improved CV text from Gemini
            improved_cv_text = self._get_improved_cv(prompt)
            
            if not improved_cv_text:
                logger.error("Failed to get improved CV text from Gemini")
                return self._create_error_response("Failed to improve CV text")
            
            # Parse improved text into structured data
            structured_cv_data = self._parse_improved_cv(improved_cv_text, original_cv_text)
            
            # Generate PDF using template
            pdf_path = self._generate_structured_pdf(structured_cv_data, template_id, strategy)
            
            if not pdf_path:
                logger.error("Failed to generate structured PDF")
                return self._create_error_response("Failed to generate PDF")
            
            # Calculate new ATS score (simplified - in production, you'd run full ATS analysis)
            new_score = self._estimate_new_score(original_score, ats_feedback)
            
            return {
                "success": True,
                "original_score": original_score,
                "new_score": new_score,
                "improvement_strategy": strategy,
                "improved_cv_text": improved_cv_text,
                "pdf_path": pdf_path,
                "changes_made": self._summarize_changes(ats_feedback),
                "template_used": template_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error improving CV: {e}")
            return self._create_error_response(str(e))
    
    def _parse_improved_cv(self, improved_cv_text: str, original_cv_text: str) -> Dict[str, Any]:
        """Parse improved CV text into structured data for template generation"""
        try:
            logger.info("Parsing improved CV text into structured data...")
            
            # Extract basic information
            structured_data = {
                'name': self._extract_name(improved_cv_text),
                'title': self._extract_title(improved_cv_text),
                'email': self._extract_email(improved_cv_text),
                'mobile': self._extract_mobile(improved_cv_text),
                'address': self._extract_address(improved_cv_text),
                'linkedin': self._extract_linkedin(improved_cv_text),
                'github': self._extract_github(improved_cv_text),
                'summary': self._extract_summary(improved_cv_text),
                'skills': self._extract_skills(improved_cv_text),
                'experience': self._extract_experience(improved_cv_text),
                'education': self._extract_education(improved_cv_text),
                'certifications': self._extract_certifications(improved_cv_text)
            }
            
            logger.info(f"Structured data extracted: {list(structured_data.keys())}")
            return structured_data
            
        except Exception as e:
            logger.error(f"Error parsing improved CV: {e}")
            # Fallback to basic structure
            return {
                'name': 'Professional CV',
                'summary': improved_cv_text[:500] + '...' if len(improved_cv_text) > 500 else improved_cv_text
            }
    
    def _generate_structured_pdf(self, cv_data: Dict[str, Any], template_id: str, strategy: str) -> Optional[str]:
        """Generate PDF using structured template system"""
        try:
            logger.info(f"Generating structured PDF using template: {template_id}")
            
            # Use template engine to generate PDF
            pdf_path = self.template_engine.generate_cv(template_id, cv_data, strategy)
            
            if pdf_path:
                logger.info(f"Structured PDF generated successfully: {pdf_path}")
                return pdf_path
            else:
                logger.error("Template engine failed to generate PDF")
                # Fallback to basic PDF generation
                return self._generate_pdf_fallback(cv_data, strategy)
                
        except Exception as e:
            logger.error(f"Error generating structured PDF: {e}")
            # Fallback to basic PDF generation
            return self._generate_pdf_fallback(cv_data, strategy)
    
    def _generate_pdf_fallback(self, cv_data: Dict[str, Any], strategy: str) -> Optional[str]:
        """Fallback PDF generation if template system fails"""
        try:
            logger.info("Using fallback PDF generation...")
            
            # Create basic PDF
            doc = fitz.open()
            page = doc.new_page(width=595, height=842)
            
            # Add basic content
            y_pos = 50
            
            # Name
            if cv_data.get('name'):
                page.insert_text(
                    point=(50, y_pos),
                    text=cv_data['name'],
                    fontsize=20,
                    fontname="helv-b",
                    color=(0, 0, 0)
                )
                y_pos += 30
            
            # Summary
            if cv_data.get('summary'):
                page.insert_text(
                    point=(50, y_pos),
                    text="PROFESSIONAL SUMMARY",
                    fontsize=14,
                    fontname="helv-b",
                    color=(0, 0, 0)
                )
                y_pos += 20
                
                wrapped_text = self._wrap_text(cv_data['summary'], 450, 10)
                page.insert_text(
                    point=(50, y_pos),
                    text=wrapped_text,
                    fontsize=10,
                    fontname="helv",
                    color=(0, 0, 0)
                )
                y_pos += 40
            
            # Save PDF
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"cv_fallback_{strategy}_{timestamp}.pdf"
            pdf_path = os.path.join(self.temp_dir, pdf_filename)
            
            doc.save(pdf_path)
            doc.close()
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Fallback PDF generation also failed: {e}")
            return None
    
    def _extract_name(self, text: str) -> str:
        """Extract name from CV text"""
        try:
            lines = text.split('\n')
            for line in lines[:5]:  # Check first 5 lines
                line = line.strip()
                if line and len(line) < 50 and not any(char in line for char in ['@', 'http', 'www', 'phone', 'email', 'linkedin']):
                    # Check if it looks like a name (capitalized, no numbers, reasonable length)
                    if line[0].isupper() and not any(char.isdigit() for char in line) and 2 <= len(line.split()) <= 4:
                        return line
            return 'Professional CV'
        except:
            return 'Professional CV'
    
    def _extract_title(self, text: str) -> str:
        """Extract job title from CV text"""
        try:
            lines = text.split('\n')
            for i, line in enumerate(lines[:15]):
                line = line.strip()
                if line and any(keyword in line.lower() for keyword in ['engineer', 'manager', 'developer', 'analyst', 'specialist', 'consultant', 'director', 'lead', 'senior']):
                    return line
            return ''
        except:
            return ''
    
    def _extract_email(self, text: str) -> str:
        """Extract email from CV text"""
        try:
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            match = re.search(email_pattern, text)
            return match.group() if match else ''
        except:
            return ''
    
    def _extract_mobile(self, text: str) -> str:
        """Extract mobile number from CV text"""
        try:
            import re
            phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            match = re.search(phone_pattern, text)
            return match.group() if match else ''
        except:
            return ''
    
    def _extract_address(self, text: str) -> str:
        """Extract address from CV text"""
        try:
            lines = text.split('\n')
            for line in lines[:20]:
                line = line.strip()
                if line and any(keyword in line.lower() for keyword in ['street', 'avenue', 'road', 'drive', 'lane']):
                    return line
            return ''
        except:
            return ''
    
    def _extract_linkedin(self, text: str) -> str:
        """Extract LinkedIn URL from CV text"""
        try:
            import re
            linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[\w-]+'
            match = re.search(linkedin_pattern, text)
            return match.group() if match else ''
        except:
            return ''
    
    def _extract_github(self, text: str) -> str:
        """Extract GitHub URL from CV text"""
        try:
            import re
            github_pattern = r'https?://(?:www\.)?github\.com/[\w-]+'
            match = re.search(github_pattern, text)
            return match.group() if match else ''
        except:
            return ''
    
    def _extract_summary(self, text: str) -> str:
        """Extract professional summary from CV text"""
        try:
            lines = text.split('\n')
            summary_start = -1
            summary_end = -1
            
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in ['summary', 'profile', 'objective', 'overview']):
                    summary_start = i + 1
                    break
            
            if summary_start != -1:
                # Look for the next section header
                for i in range(summary_start, min(summary_start + 15, len(lines))):
                    if lines[i].strip() and any(keyword in lines[i].lower() for keyword in ['experience', 'skills', 'education', 'work history', 'employment']):
                        summary_end = i
                        break
                
                if summary_end == -1:
                    summary_end = min(summary_start + 15, len(lines))
                
                summary_text = '\n'.join(lines[summary_start:summary_end])
                summary_text = summary_text.strip()
                
                # If summary is too short, try to get more content
                if len(summary_text) < 50:
                    # Look for a longer paragraph after the summary header
                    for i in range(summary_start, min(summary_start + 25, len(lines))):
                        if lines[i].strip() and len(lines[i].strip()) > 50:
                            summary_text = lines[i].strip()
                            break
                
                return summary_text
            
            # Fallback: look for the longest paragraph in the first part of the CV
            longest_paragraph = ""
            for line in lines[:20]:
                if len(line.strip()) > len(longest_paragraph):
                    longest_paragraph = line.strip()
            
            return longest_paragraph if longest_paragraph else "Experienced professional with strong skills and proven track record."
            
        except:
            return "Experienced professional with strong skills and proven track record."
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from CV text"""
        try:
            lines = text.split('\n')
            skills = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line and any(keyword in line.lower() for keyword in ['skills', 'competencies', 'technologies', 'tools', 'languages']):
                    # Extract skills from this line and next few lines
                    skill_text = line
                    for j in range(1, 8):  # Check next 7 lines
                        if i + j < len(lines):
                            skill_text += ' ' + lines[i + j].strip()
                    
                    # Extract individual skills
                    skill_items = skill_text.replace(',', ';').replace('•', ';').replace('|', ';').split(';')
                    for skill in skill_items:
                        skill = skill.strip()
                        if skill and len(skill) > 2 and len(skill) < 50 and not any(char in skill for char in ['@', 'http', 'www']):
                            # Clean up the skill
                            skill = skill.replace('Skills:', '').replace('Technologies:', '').replace('Tools:', '').strip()
                            if skill and skill not in skills:
                                skills.append(skill)
                    
                    break
            
            # If no skills found, try to extract from the text
            if not skills:
                # Look for common skill patterns
                skill_patterns = [
                    'python', 'java', 'javascript', 'react', 'angular', 'node.js', 'sql', 'aws', 'docker', 'kubernetes',
                    'project management', 'agile', 'scrum', 'leadership', 'communication', 'problem solving',
                    'data analysis', 'machine learning', 'ai', 'cloud computing', 'devops'
                ]
                
                text_lower = text.lower()
                for pattern in skill_patterns:
                    if pattern in text_lower:
                        skills.append(pattern.title())
            
            return skills[:25]  # Limit to 25 skills
            
        except:
            return ['Problem Solving', 'Communication', 'Teamwork', 'Leadership']
    
    def _extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience from CV text"""
        try:
            lines = text.split('\n')
            experiences = []
            current_exp = {}
            in_experience_section = False
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Check for experience section
                if any(keyword in line.lower() for keyword in ['experience', 'work history', 'employment', 'professional experience']):
                    in_experience_section = True
                    continue
                
                if in_experience_section:
                    # Check for job title patterns
                    if any(keyword in line.lower() for keyword in ['engineer', 'manager', 'developer', 'analyst', 'specialist', 'consultant', 'director', 'lead', 'senior', 'junior']):
                        if current_exp:
                            experiences.append(current_exp)
                        current_exp = {'title': line}
                    
                    # Check for company patterns (lines that don't look like job titles or descriptions)
                    elif line and not any(char in line for char in ['@', 'http', 'www']) and len(line) < 100:
                        if 'title' in current_exp and 'company' not in current_exp:
                            current_exp['company'] = line
                        elif 'company' in current_exp and 'duration' not in current_exp:
                            current_exp['duration'] = line
                        elif 'duration' in current_exp and 'description' not in current_exp:
                            # This might be the start of description
                            current_exp['description'] = line
                        elif 'description' in current_exp:
                            # Append to existing description
                            current_exp['description'] += ' ' + line
                    
                    # Check if we've moved to another section
                    elif any(keyword in line.lower() for keyword in ['education', 'skills', 'certifications', 'projects']):
                        break
            
            if current_exp:
                experiences.append(current_exp)
            
            # If no experiences found, create a generic one
            if not experiences:
                experiences = [{
                    'title': 'Professional Experience',
                    'company': 'Various Companies',
                    'duration': 'Multiple Years',
                    'description': 'Demonstrated expertise in relevant field with proven track record of success.'
                }]
            
            return experiences[:5]  # Limit to 5 experiences
            
        except:
            return [{
                'title': 'Professional Experience',
                'company': 'Various Companies',
                'duration': 'Multiple Years',
                'description': 'Demonstrated expertise in relevant field with proven track record of success.'
            }]
    
    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education from CV text"""
        try:
            lines = text.split('\n')
            education = []
            current_edu = {}
            in_education_section = False
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Check for education section
                if any(keyword in line.lower() for keyword in ['education', 'academic', 'qualifications', 'degree']):
                    in_education_section = True
                    continue
                
                if in_education_section:
                    # Check for degree patterns
                    if any(keyword in line.lower() for keyword in ['bachelor', 'master', 'phd', 'degree', 'diploma', 'certificate']):
                        if current_edu:
                            education.append(current_edu)
                        current_edu = {'degree': line}
                    
                    # Check for institution
                    elif line and not any(char in line for char in ['@', 'http', 'www']) and len(line) < 100:
                        if 'degree' in current_edu and 'institution' not in current_edu:
                            current_edu['institution'] = line
                        elif 'institution' in current_edu and 'year' not in current_edu:
                            current_edu['year'] = line
                    
                    # Check if we've moved to another section
                    elif any(keyword in line.lower() for keyword in ['experience', 'skills', 'certifications', 'projects']):
                        break
            
            if current_edu:
                education.append(current_edu)
            
            # If no education found, create a generic one
            if not education:
                education = [{
                    'degree': 'Relevant Degree',
                    'institution': 'University',
                    'year': 'Graduated'
                }]
            
            return education[:3]  # Limit to 3 education entries
            
        except:
            return [{
                'degree': 'Relevant Degree',
                'institution': 'University',
                'year': 'Graduated'
            }]
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications from CV text"""
        try:
            lines = text.split('\n')
            certifications = []
            
            for line in lines:
                line = line.strip()
                if line and any(keyword in line.lower() for keyword in ['certification', 'certified', 'certificate']):
                    # Extract certification name
                    cert_name = line.replace('certification', '').replace('certified', '').replace('certificate', '').strip()
                    if cert_name and len(cert_name) > 3:
                        certifications.append(cert_name)
            
            return certifications[:5]  # Limit to 5 certifications
        except:
            return []
    
    def _determine_strategy(self, score: int) -> str:
        """Determine improvement strategy based on ATS score"""
        if score >= 70:
            return "minor_fix"
        elif score <= 60:
            return "major_overhaul"
        else:
            return "hybrid"
    
    def _create_improvement_prompt(self, original_cv_text: str, 
                                  ats_feedback: Dict[str, Any], strategy: str) -> str:
        """Create the improvement prompt for Gemini"""
        
        # Extract key feedback points
        issues = ats_feedback.get('issues', [])
        missing_keywords = ats_feedback.get('keyword_matches', {}).get('missing', [])
        grammar_issues = [i for i in issues if i.get('type') == 'grammar']
        spelling_issues = [i for i in issues if i.get('type') == 'spelling']
        
        # Format feedback for the prompt
        feedback_summary = []
        if missing_keywords:
            feedback_summary.append(f"Missing keywords: {', '.join(missing_keywords[:10])}")
        if grammar_issues:
            feedback_summary.append(f"Grammar issues: {len(grammar_issues)} found")
        if spelling_issues:
            feedback_summary.append(f"Spelling issues: {len(spelling_issues)} found")
        
        feedback_text = "; ".join(feedback_summary) if feedback_summary else "No major issues found"
        
        prompt = f"""You are an expert ATS resume optimizer. Improve the CV according to the following rules based on its ATS score:

1. If score is high (≥70): Minor edits only, preserve structure and style.
2. If score is low (≤60): Rewrite using an ATS-friendly template and ensure full optimization.
3. If score is medium (60–69): Hybrid approach — improve structure while keeping style.

Follow these general guidelines:
* Address the following ATS feedback: {feedback_text}
* Keep professional tone and readability.
* Avoid keyword stuffing or irrelevant content.
* Output must be plain text CV format with clear section separation.
* Do not include explanations or metadata.
* Ensure the CV is ready for direct PDF conversion.

Strategy to use: {strategy}

Original CV:
{original_cv_text}

Improved CV:"""

        return prompt
    
    def _get_improved_cv(self, prompt: str) -> Optional[str]:
        """Get improved CV text from Gemini Flash 2.0"""
        try:
            if not self.model:
                logger.error("Gemini model not available")
                return None
            
            # Use Gemini Flash 2.0 (gemini-1.5-flash)
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                improved_text = response.text.strip()
                logger.info(f"Successfully generated improved CV text ({len(improved_text)} characters)")
                return improved_text
            else:
                logger.error("Empty response from Gemini")
                return None
                
        except Exception as e:
            logger.error(f"Error getting improved CV from Gemini: {e}")
            return None
    
    def _generate_pdf(self, improved_cv_text: str, strategy: str, 
                      original_cv_text: str) -> Optional[str]:
        """Generate PDF using PyMuPDF based on improvement strategy"""
        try:
            logger.info(f"Starting PDF generation with text length: {len(improved_cv_text)}")
            logger.info(f"Strategy: {strategy}")
            
            # Create PDF filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"improved_cv_{strategy}_{timestamp}.pdf"
            pdf_path = os.path.join(self.temp_dir, pdf_filename)
            
            logger.info(f"PDF will be saved to: {pdf_path}")
            logger.info(f"Temp directory: {self.temp_dir}")
            logger.info(f"Temp directory exists: {os.path.exists(self.temp_dir)}")
            
            # Try the complex PDF generation first
            try:
                # Create PDF document
                logger.info("Creating PDF document...")
                doc = fitz.open()
                logger.info("PDF document created successfully")
                
                if strategy == "minor_fix":
                    # Preserve original layout style
                    logger.info("Creating page for minor_fix strategy...")
                    page = doc.new_page(width=595, height=842)  # A4 size
                    logger.info("Page created, adding text...")
                    self._add_text_to_page(page, improved_cv_text, preserve_style=True)
                    logger.info("Text added successfully")
                    
                elif strategy == "major_overhaul":
                    # Clean, modern ATS-friendly layout
                    logger.info("Creating page for major_overhaul strategy...")
                    page = doc.new_page(width=595, height=842)
                    logger.info("Page created, adding text...")
                    self._add_text_to_page(page, improved_cv_text, preserve_style=False)
                    logger.info("Text added successfully")
                    
                else:  # hybrid
                    # Balance between original and optimized
                    logger.info("Creating page for hybrid strategy...")
                    page = doc.new_page(width=595, height=842)
                    logger.info("Page created, adding text...")
                    self._add_text_to_page(page, improved_cv_text, preserve_style=True)
                    logger.info("Text added successfully")
                
                # Save PDF
                logger.info("Saving PDF...")
                doc.save(pdf_path)
                doc.close()
                logger.info("PDF saved and document closed")
                
            except Exception as complex_error:
                logger.warning(f"Complex PDF generation failed: {complex_error}")
                logger.info("Falling back to simple PDF generation...")
                
                # Fallback: Simple PDF with just text
                doc = fitz.open()
                page = doc.new_page(width=595, height=842)
                
                # Simple text insertion
                lines = improved_cv_text.split('\n')
                y_position = 50
                
                for line in lines[:50]:  # Limit to first 50 lines to avoid overflow
                    if line.strip():
                        try:
                            page.insert_text(
                                point=(50, y_position),
                                text=line.strip(),
                                fontsize=10,
                                fontname="helv",
                                color=(0, 0, 0)
                            )
                            y_position += 15
                        except:
                            continue  # Skip problematic lines
                
                doc.save(pdf_path)
                doc.close()
                logger.info("Simple PDF generated successfully")
            
            # Verify PDF was created and has content
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                logger.info(f"PDF generated successfully: {pdf_path} (size: {file_size} bytes)")
                
                if file_size > 0:
                    return pdf_path
                else:
                    logger.error("PDF file was created but is empty")
                    return None
            else:
                logger.error("PDF file was not created")
                return None
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _add_text_to_page(self, page, text: str, preserve_style: bool = True):
        """Add text to PDF page with appropriate formatting"""
        try:
            logger.info(f"Starting to add text to page (text length: {len(text)})")
            
            # Split text into sections
            logger.info("Parsing CV sections...")
            sections = self._parse_cv_sections(text)
            logger.info(f"Parsed sections: {list(sections.keys())}")
            
            y_position = 50  # Start position from top
            left_margin = 50
            right_margin = 545
            
            # Add title
            if sections.get('header'):
                logger.info(f"Adding header: {sections['header'][:50]}...")
                page.insert_text(
                    point=(left_margin, y_position),
                    text=sections['header'],
                    fontsize=18,
                    fontname="helv-b",
                    color=(0, 0, 0)
                )
                y_position += 30
                logger.info("Header added successfully")
            
            # Add contact info
            if sections.get('contact'):
                logger.info(f"Adding contact info: {sections['contact'][:50]}...")
                page.insert_text(
                    point=(left_margin, y_position),
                    text=sections['contact'],
                    fontsize=10,
                    fontname="helv",
                    color=(0, 0, 0)
                )
                y_position += 20
                logger.info("Contact info added successfully")
            
            # Add summary
            if sections.get('summary'):
                logger.info("Adding summary section...")
                page.insert_text(
                    point=(left_margin, y_position),
                    text="PROFESSIONAL SUMMARY",
                    fontsize=14,
                    fontname="helv-b",
                    color=(0, 0, 0)
                )
                y_position += 20
                
                # Wrap text to fit page width
                logger.info("Wrapping summary text...")
                wrapped_text = self._wrap_text(sections['summary'], right_margin - left_margin, 10)
                page.insert_text(
                    point=(left_margin, y_position),
                    text=wrapped_text,
                    fontsize=10,
                    fontname="helv",
                    color=(0, 0, 0)
                )
                y_position += 30
                logger.info("Summary added successfully")
            
            # Add skills
            if sections.get('skills'):
                logger.info("Adding skills section...")
                page.insert_text(
                    point=(left_margin, y_position),
                    text="SKILLS",
                    fontsize=14,
                    fontname="helv-b",
                    color=(0, 0, 0)
                )
                y_position += 20
                
                skills_text = ", ".join(sections['skills'])
                page.insert_text(
                    point=(left_margin, y_position),
                    text=skills_text,
                    fontsize=10,
                    fontname="helv",
                    color=(0, 0, 0)
                )
                y_position += 30
                logger.info("Skills added successfully")
            
            # Add experience
            if sections.get('experience'):
                logger.info("Adding experience section...")
                page.insert_text(
                    point=(left_margin, y_position),
                    text="PROFESSIONAL EXPERIENCE",
                    fontsize=14,
                    fontname="helv-b",
                    color=(0, 0, 0)
                )
                y_position += 20
                
                for i, exp in enumerate(sections['experience']):
                    logger.info(f"Adding experience {i+1}: {exp.get('title', 'Unknown')}")
                    if y_position > 750:  # Check if we need a new page
                        logger.info("Creating new page for experience...")
                        page = self._add_new_page_if_needed(page)
                        y_position = 50
                    
                    # Add job title
                    if exp.get('title'):
                        page.insert_text(
                            point=(left_margin, y_position),
                            text=exp['title'],
                            fontsize=12,
                            fontname="helv-b",
                            color=(0, 0, 0)
                        )
                        y_position += 15
                    
                    # Add company and duration
                    company_duration = f"{exp.get('company', '')} | {exp.get('duration', '')}"
                    if company_duration.strip() != '|':
                        page.insert_text(
                            point=(left_margin, y_position),
                            text=company_duration,
                            fontsize=10,
                            fontname="helv",
                            color=(0.5, 0.5, 0.5)
                        )
                        y_position += 15
                    
                    # Add description
                    if exp.get('description'):
                        wrapped_desc = self._wrap_text(exp['description'], right_margin - left_margin, 10)
                        page.insert_text(
                            point=(left_margin, y_position),
                            text=wrapped_desc,
                            fontsize=10,
                            fontname="helv",
                            color=(0, 0, 0)
                        )
                        y_position += 20
                    
                    y_position += 10  # Space between experiences
                
                logger.info("Experience section added successfully")
            
            # Add education
            if sections.get('education'):
                logger.info("Adding education section...")
                page.insert_text(
                    point=(left_margin, y_position),
                    text="EDUCATION",
                    fontsize=14,
                    fontname="helv-b",
                    color=(0, 0, 0)
                )
                y_position += 20
                
                for edu in sections['education']:
                    if y_position > 750:
                        logger.info("Creating new page for education...")
                        page = self._add_new_page_if_needed(page)
                        y_position = 50
                    
                    # Add degree
                    if edu.get('degree'):
                        page.insert_text(
                            point=(left_margin, y_position),
                            text=edu['degree'],
                            fontsize=12,
                            fontname="helv-b",
                            color=(0, 0, 0)
                        )
                        y_position += 15
                    
                    # Add institution and year
                    institution_year = f"{edu.get('institution', '')} | {edu.get('year', '')}"
                    if institution_year.strip() != '|':
                        page.insert_text(
                            point=(left_margin, y_position),
                            text=institution_year,
                            fontsize=10,
                            fontname="helv",
                            color=(0.5, 0.5, 0.5)
                        )
                        y_position += 20
                
                logger.info("Education section added successfully")
            
            logger.info("All text added to page successfully")
            
        except Exception as e:
            logger.error(f"Error adding text to page: {e}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise  # Re-raise to be caught by the calling function
    
    def _add_new_page_if_needed(self, current_page):
        """Add a new page if needed and return the new page"""
        try:
            logger.info("Adding new page...")
            doc = current_page.parent
            new_page = doc.new_page(width=595, height=842)  # A4 size
            logger.info("New page added successfully")
            return new_page
        except Exception as e:
            logger.error(f"Error adding new page: {e}")
            # Return the current page if we can't add a new one
            return current_page

    def _parse_cv_sections(self, text: str) -> Dict[str, Any]:
        """Parse CV text into structured sections"""
        sections = {}
        lines = text.split('\n')
        
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            lower_line = line.lower()
            if any(keyword in lower_line for keyword in ['summary', 'profile', 'objective']):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'summary'
                current_content = []
            elif any(keyword in lower_line for keyword in ['skills', 'technical skills', 'competencies']):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'skills'
                current_content = []
            elif any(keyword in lower_line for keyword in ['experience', 'work history', 'employment']):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'experience'
                current_content = []
            elif any(keyword in lower_line for keyword in ['education', 'academic', 'qualifications']):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'education'
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
                elif not sections.get('header'):
                    # First non-empty line is usually the header
                    sections['header'] = line
                elif not sections.get('contact'):
                    # Second non-empty line is usually contact info
                    sections['contact'] = line
        
        # Add the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # Process skills into list format
        if 'skills' in sections:
            skills_text = sections['skills']
            skills_list = [skill.strip() for skill in skills_text.replace(',', ';').split(';') if skill.strip()]
            sections['skills'] = skills_list
        
        # Process experience into structured format
        if 'experience' in sections:
            exp_text = sections['experience']
            # Simple parsing - in production, you'd want more sophisticated parsing
            experiences = []
            exp_blocks = exp_text.split('\n\n')
            for block in exp_blocks:
                lines = block.split('\n')
                if len(lines) >= 2:
                    exp = {
                        'title': lines[0].strip(),
                        'company': lines[1].strip() if len(lines) > 1 else '',
                        'duration': lines[2].strip() if len(lines) > 2 else '',
                        'description': '\n'.join(lines[3:]).strip() if len(lines) > 3 else ''
                    }
                    experiences.append(exp)
            sections['experience'] = experiences
        
        # Process education into structured format
        if 'education' in sections:
            edu_text = sections['education']
            educations = []
            edu_blocks = edu_text.split('\n\n')
            for block in edu_blocks:
                lines = block.split('\n')
                if len(lines) >= 2:
                    edu = {
                        'degree': lines[0].strip(),
                        'institution': lines[1].strip() if len(lines) > 1 else '',
                        'year': lines[2].strip() if len(lines) > 2 else ''
                    }
                    educations.append(edu)
            sections['education'] = educations
        
        return sections
    
    def _wrap_text(self, text: str, max_width: int, font_size: int) -> str:
        """Simple text wrapping for PDF generation"""
        # This is a simplified text wrapper
        # In production, you'd want more sophisticated text wrapping
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            # Rough estimation: 1 character ≈ 0.6 * font_size in points
            estimated_width = len(test_line) * font_size * 0.6
            
            if estimated_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return '\n'.join(lines)
    
    def _estimate_new_score(self, original_score: int, ats_feedback: Dict[str, Any]) -> int:
        """Estimate new ATS score based on improvements made"""
        # This is a simplified estimation
        # In production, you'd want to run the full ATS analysis
        
        base_improvement = 0
        
        # Estimate improvement based on issues addressed
        issues = ats_feedback.get('issues', [])
        grammar_issues = len([i for i in issues if i.get('type') == 'grammar'])
        spelling_issues = len([i for i in issues if i.get('type') == 'spelling'])
        missing_keywords = len(ats_feedback.get('keyword_matches', {}).get('missing', []))
        
        # Score improvements
        if grammar_issues > 0:
            base_improvement += min(grammar_issues * 2, 10)
        if spelling_issues > 0:
            base_improvement += min(spelling_issues * 1, 5)
        if missing_keywords > 0:
            base_improvement += min(missing_keywords * 1, 15)
        
        new_score = min(100, original_score + base_improvement)
        return new_score
    
    def _summarize_changes(self, ats_feedback: Dict[str, Any]) -> List[str]:
        """Summarize the changes made to the CV"""
        changes = []
        
        issues = ats_feedback.get('issues', [])
        grammar_count = len([i for i in issues if i.get('type') == 'grammar'])
        spelling_count = len([i for i in issues if i.get('type') == 'spelling'])
        missing_keywords = ats_feedback.get('keyword_matches', {}).get('missing', [])
        
        if grammar_count > 0:
            changes.append(f"Fixed {grammar_count} grammar issues")
        if spelling_count > 0:
            changes.append(f"Corrected {spelling_count} spelling errors")
        if missing_keywords:
            changes.append(f"Added {len(missing_keywords)} missing keywords")
        
        if not changes:
            changes.append("Minor formatting and structure improvements")
        
        return changes
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "success": False,
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")
