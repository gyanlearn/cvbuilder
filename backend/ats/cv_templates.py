import logging
import fitz  # PyMuPDF
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class CVTemplateEngine:
    """
    Professional CV template engine with multiple format options
    """
    
    def __init__(self):
        self.templates = {
            'modern_professional': self._create_modern_professional_template,
            'creative_professional': self._create_creative_professional_template,
            'academic_research': self._create_academic_research_template,
            'executive_leadership': self._create_executive_leadership_template
        }
        
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available templates with descriptions"""
        return [
            {
                'id': 'modern_professional',
                'name': 'Modern Professional',
                'description': 'Clean, ATS-friendly corporate style with clear hierarchy',
                'best_for': 'Corporate jobs, traditional industries, ATS optimization'
            },
            {
                'id': 'creative_professional',
                'name': 'Creative Professional',
                'description': 'Modern design with visual hierarchy and creative elements',
                'best_for': 'Creative roles, design, marketing, modern companies'
            },
            {
                'id': 'academic_research',
                'name': 'Academic/Research',
                'description': 'Formal academic style with publication focus',
                'best_for': 'Research positions, academia, scientific roles'
            },
            {
                'id': 'executive_leadership',
                'name': 'Executive/Leadership',
                'description': 'Senior-level format emphasizing achievements and leadership',
                'best_for': 'Senior management, executive roles, leadership positions'
            }
        ]
    
    def generate_cv(self, template_id: str, cv_data: Dict[str, Any], 
                    improvement_strategy: str) -> Optional[str]:
        """Generate CV using specified template"""
        try:
            if template_id not in self.templates:
                logger.error(f"Template {template_id} not found")
                return None
                
            logger.info(f"Generating CV using template: {template_id}")
            logger.info(f"Improvement strategy: {improvement_strategy}")
            
            # Create PDF using template
            pdf_path = self.templates[template_id](cv_data, improvement_strategy)
            
            if pdf_path and os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                logger.info(f"CV generated successfully: {pdf_path} (size: {file_size} bytes)")
                return pdf_path
            else:
                logger.error("Template failed to generate PDF")
                return None
                
        except Exception as e:
            logger.error(f"Error generating CV with template {template_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _create_modern_professional_template(self, cv_data: Dict[str, Any], 
                                           improvement_strategy: str) -> Optional[str]:
        """Create modern professional CV template"""
        try:
            logger.info("Creating modern professional template...")
            logger.info(f"CV data keys: {list(cv_data.keys())}")
            logger.info(f"CV data sample: {str(cv_data)[:200]}...")
            
            # Create PDF
            doc = fitz.open()
            page = doc.new_page(width=595, height=842)  # A4
            logger.info("PDF document and page created")
            
            # Header Section
            logger.info("Adding header section...")
            self._add_modern_header(page, cv_data)
            logger.info("Header section added")
            
            # Professional Summary
            if cv_data.get('summary'):
                logger.info(f"Adding summary section (length: {len(cv_data['summary'])})")
                self._add_modern_summary(page, cv_data['summary'])
                logger.info("Summary section added")
            else:
                logger.warning("No summary found in CV data")
            
            # Core Skills
            if cv_data.get('skills'):
                logger.info(f"Adding skills section ({len(cv_data['skills'])} skills)")
                self._add_modern_skills(page, cv_data['skills'])
                logger.info("Skills section added")
            else:
                logger.warning("No skills found in CV data")
            
            # Professional Experience
            if cv_data.get('experience'):
                logger.info(f"Adding experience section ({len(cv_data['experience'])} experiences)")
                self._add_modern_experience(page, cv_data['experience'])
                logger.info("Experience section added")
            else:
                logger.warning("No experience found in CV data")
            
            # Education
            if cv_data.get('education'):
                logger.info(f"Adding education section ({len(cv_data['education'])} entries)")
                self._add_modern_education(page, cv_data['education'])
                logger.info("Education section added")
            else:
                logger.warning("No education found in CV data")
            
            # Certifications
            if cv_data.get('certifications'):
                logger.info(f"Adding certifications section ({len(cv_data['certifications'])} certifications)")
                self._add_modern_certifications(page, cv_data['certifications'])
                logger.info("Certifications section added")
            else:
                logger.warning("No certifications found in CV data")
            
            # Save PDF
            logger.info("Saving PDF...")
            pdf_path = self._save_template_pdf(doc, 'modern_professional')
            logger.info(f"PDF saved to: {pdf_path}")
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error creating modern professional template: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _create_creative_professional_template(self, cv_data: Dict[str, Any], 
                                             improvement_strategy: str) -> Optional[str]:
        """Create creative professional CV template"""
        try:
            # Create PDF
            doc = fitz.open()
            page = doc.new_page(width=595, height=842)  # A4
            
            # Creative Header with accent color
            self._add_creative_header(page, cv_data)
            
            # Professional Summary with modern styling
            if cv_data.get('summary'):
                self._add_creative_summary(page, cv_data['summary'])
            
            # Skills with visual grouping
            if cv_data.get('skills'):
                self._add_creative_skills(page, cv_data['skills'])
            
            # Experience with timeline design
            if cv_data.get('experience'):
                self._add_creative_experience(page, cv_data['experience'])
            
            # Education with modern layout
            if cv_data.get('education'):
                self._add_creative_education(page, cv_data['education'])
            
            # Save PDF
            pdf_path = self._save_template_pdf(doc, 'creative_professional')
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error creating creative professional template: {e}")
            return None
    
    def _create_academic_research_template(self, cv_data: Dict[str, Any], 
                                         improvement_strategy: str) -> Optional[str]:
        """Create academic/research CV template"""
        try:
            # Create PDF
            doc = fitz.open()
            page = doc.new_page(width=595, height=842)  # A4
            
            # Academic Header
            self._add_academic_header(page, cv_data)
            
            # Research Summary
            if cv_data.get('summary'):
                self._add_academic_summary(page, cv_data['summary'])
            
            # Research Experience
            if cv_data.get('experience'):
                self._add_academic_experience(page, cv_data['experience'])
            
            # Education
            if cv_data.get('education'):
                self._add_academic_education(page, cv_data['education'])
            
            # Publications (if available)
            if cv_data.get('publications'):
                self._add_academic_publications(page, cv_data['publications'])
            
            # Save PDF
            pdf_path = self._save_template_pdf(doc, 'academic_research')
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error creating academic research template: {e}")
            return None
    
    def _create_executive_leadership_template(self, cv_data: Dict[str, Any], 
                                            improvement_strategy: str) -> Optional[str]:
        """Create executive/leadership CV template"""
        try:
            # Create PDF
            doc = fitz.open()
            page = doc.new_page(width=595, height=842)  # A4
            
            # Executive Header
            self._add_executive_header(page, cv_data)
            
            # Executive Summary
            if cv_data.get('summary'):
                self._add_executive_summary(page, cv_data['summary'])
            
            # Leadership Experience
            if cv_data.get('experience'):
                self._add_executive_experience(page, cv_data['experience'])
            
            # Education
            if cv_data.get('education'):
                self._add_executive_education(page, cv_data['education'])
            
            # Board Positions & Leadership
            if cv_data.get('leadership'):
                self._add_executive_leadership(page, cv_data['leadership'])
            
            # Save PDF
            pdf_path = self._save_template_pdf(doc, 'executive_leadership')
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error creating executive leadership template: {e}")
            return None
    
    def _save_template_pdf(self, doc, template_name: str) -> Optional[str]:
        """Save template PDF to temporary directory"""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"cv_{template_name}_{timestamp}.pdf"
            
            # Create temp directory if it doesn't exist
            temp_dir = "/tmp/cv_templates"
            os.makedirs(temp_dir, exist_ok=True)
            
            pdf_path = os.path.join(temp_dir, pdf_filename)
            doc.save(pdf_path)
            doc.close()
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error saving template PDF: {e}")
            return None
    
    # ===== MODERN PROFESSIONAL TEMPLATE STYLING =====
    
    def _add_modern_header(self, page, cv_data: Dict[str, Any]):
        """Add modern professional header"""
        try:
            # Name (large, bold)
            name = cv_data.get('name', 'Professional CV')
            page.insert_text(
                point=(50, 50),
                text=name.upper(),
                fontsize=24,
                fontname="helv-b",
                color=(0.1, 0.1, 0.1)
            )
            
            # Title/Position
            title = cv_data.get('title', '')
            if title:
                page.insert_text(
                    point=(50, 80),
                    text=title,
                    fontsize=14,
                    fontname="helv",
                    color=(0.3, 0.3, 0.3)
                )
            
            # Contact Information (right-aligned)
            contact_info = []
            if cv_data.get('email'):
                contact_info.append(cv_data['email'])
            if cv_data.get('mobile'):
                contact_info.append(cv_data['mobile'])
            if cv_data.get('address'):
                contact_info.append(cv_data['address'])
            if cv_data.get('linkedin'):
                contact_info.append(f"LinkedIn: {cv_data['linkedin']}")
            
            y_pos = 50
            for contact in contact_info:
                page.insert_text(
                    point=(400, y_pos),
                    text=contact,
                    fontsize=10,
                    fontname="helv",
                    color=(0.4, 0.4, 0.4)
                )
                y_pos += 15
            
            # Horizontal line
            page.draw_line(
                start=(50, 110),
                end=(545, 110),
                color=(0.2, 0.2, 0.2),
                width=1
            )
            
        except Exception as e:
            logger.error(f"Error adding modern header: {e}")
    
    def _add_modern_summary(self, page, summary: str):
        """Add modern professional summary section"""
        try:
            # Section header
            page.insert_text(
                point=(50, 140),
                text="PROFESSIONAL SUMMARY",
                fontsize=16,
                fontname="helv-b",
                color=(0.1, 0.1, 0.1)
            )
            
            # Summary text (wrapped)
            wrapped_text = self._wrap_text(summary, 450, 11)
            page.insert_text(
                point=(50, 165),
                text=wrapped_text,
                fontsize=11,
                fontname="helv",
                color=(0.2, 0.2, 0.2)
            )
            
        except Exception as e:
            logger.error(f"Error adding modern summary: {e}")
    
    def _add_modern_skills(self, page, skills: List[str]):
        """Add modern professional skills section"""
        try:
            # Section header
            page.insert_text(
                point=(50, 220),
                text="CORE SKILLS",
                fontsize=16,
                fontname="helv-b",
                color=(0.1, 0.1, 0.1)
            )
            
            # Skills in columns
            skills_text = " • ".join(skills[:20])  # Limit to 20 skills
            wrapped_skills = self._wrap_text(skills_text, 450, 11)
            page.insert_text(
                point=(50, 245),
                text=wrapped_skills,
                fontsize=11,
                fontname="helv",
                color=(0.2, 0.2, 0.2)
            )
            
        except Exception as e:
            logger.error(f"Error adding modern skills: {e}")
    
    def _add_modern_experience(self, page, experience: List[Dict[str, Any]]):
        """Add modern professional experience section"""
        try:
            # Section header
            page.insert_text(
                point=(50, 300),
                text="PROFESSIONAL EXPERIENCE",
                fontsize=16,
                fontname="helv-b",
                color=(0.1, 0.1, 0.1)
            )
            
            y_pos = 325
            for i, exp in enumerate(experience[:5]):  # Limit to 5 experiences
                if y_pos > 750:  # Check if we need a new page
                    page = self._add_new_page_if_needed(page)
                    y_pos = 50
                
                # Job title
                if exp.get('title'):
                    page.insert_text(
                        point=(50, y_pos),
                        text=exp['title'],
                        fontsize=13,
                        fontname="helv-b",
                        color=(0.1, 0.1, 0.1)
                    )
                    y_pos += 18
                
                # Company and duration
                company_duration = f"{exp.get('company', '')} | {exp.get('duration', '')}"
                if company_duration.strip() != '|':
                    page.insert_text(
                        point=(50, y_pos),
                        text=company_duration,
                        fontsize=11,
                        fontname="helv",
                        color=(0.4, 0.4, 0.4)
                    )
                    y_pos += 15
                
                # Description
                if exp.get('description'):
                    wrapped_desc = self._wrap_text(exp['description'], 450, 10)
                    page.insert_text(
                        point=(50, y_pos),
                        text=wrapped_desc,
                        fontsize=10,
                        fontname="helv",
                        color=(0.2, 0.2, 0.2)
                    )
                    y_pos += 25
                
                y_pos += 10  # Space between experiences
                
        except Exception as e:
            logger.error(f"Error adding modern experience: {e}")
    
    def _add_modern_education(self, page, education: List[Dict[str, Any]]):
        """Add modern professional education section"""
        try:
            # Section header
            page.insert_text(
                point=(50, 500),
                text="EDUCATION",
                fontsize=16,
                fontname="helv-b",
                color=(0.1, 0.1, 0.1)
            )
            
            y_pos = 525
            for edu in education[:3]:  # Limit to 3 education entries
                if y_pos > 750:
                    page = self._add_new_page_if_needed(page)
                    y_pos = 50
                
                # Degree
                if edu.get('degree'):
                    page.insert_text(
                        point=(50, y_pos),
                        text=edu['degree'],
                        fontsize=12,
                        fontname="helv-b",
                        color=(0.1, 0.1, 0.1)
                    )
                    y_pos += 15
                
                # Institution and year
                institution_year = f"{edu.get('institution', '')} | {edu.get('year', '')}"
                if institution_year.strip() != '|':
                    page.insert_text(
                        point=(50, y_pos),
                        text=institution_year,
                        fontsize=10,
                        fontname="helv",
                        color=(0.4, 0.4, 0.4)
                    )
                    y_pos += 20
                
        except Exception as e:
            logger.error(f"Error adding modern education: {e}")
    
    def _add_modern_certifications(self, page, certifications: List[str]):
        """Add modern professional certifications section"""
        try:
            # Section header
            page.insert_text(
                point=(50, 600),
                text="CERTIFICATIONS",
                fontsize=16,
                fontname="helv-b",
                color=(0.1, 0.1, 0.1)
            )
            
            y_pos = 625
            for cert in certifications[:5]:  # Limit to 5 certifications
                if y_pos > 750:
                    page = self._add_new_page_if_needed(page)
                    y_pos = 50
                
                page.insert_text(
                    point=(50, y_pos),
                    text=f"• {cert}",
                    fontsize=10,
                    fontname="helv",
                    color=(0.2, 0.2, 0.2)
                )
                y_pos += 15
                
        except Exception as e:
            logger.error(f"Error adding modern certifications: {e}")
    
    # ===== CREATIVE PROFESSIONAL TEMPLATE STYLING =====
    
    def _add_creative_header(self, page, cv_data: Dict[str, Any]):
        """Add creative professional header with accent color"""
        try:
            # Accent color bar
            page.draw_rect(
                rect=(0, 0, 595, 120),
                color=(0.2, 0.4, 0.8),
                fill=(0.9, 0.95, 1.0)
            )
            
            # Name (large, bold, white on accent)
            name = cv_data.get('name', 'Professional CV')
            page.insert_text(
                point=(50, 50),
                text=name.upper(),
                fontsize=28,
                fontname="helv-b",
                color=(1, 1, 1)
            )
            
            # Title/Position
            title = cv_data.get('title', '')
            if title:
                page.insert_text(
                    point=(50, 85),
                    text=title,
                    fontsize=16,
                    fontname="helv",
                    color=(0.9, 0.9, 0.9)
                )
            
            # Contact Information (right-aligned)
            contact_info = []
            if cv_data.get('email'):
                contact_info.append(cv_data['email'])
            if cv_data.get('mobile'):
                contact_info.append(cv_data['mobile'])
            if cv_data.get('linkedin'):
                contact_info.append(f"LinkedIn: {cv_data['linkedin']}")
            
            y_pos = 50
            for contact in contact_info:
                page.insert_text(
                    point=(400, y_pos),
                    text=contact,
                    fontsize=11,
                    fontname="helv",
                    color=(1, 1, 1)
                )
                y_pos += 18
            
        except Exception as e:
            logger.error(f"Error adding creative header: {e}")
    
    def _add_creative_summary(self, page, summary: str):
        """Add creative professional summary with modern styling"""
        try:
            # Section header with accent color
            page.insert_text(
                point=(50, 150),
                text="PROFESSIONAL SUMMARY",
                fontsize=18,
                fontname="helv-b",
                color=(0.2, 0.4, 0.8)
            )
            
            # Summary text in a styled box
            wrapped_text = self._wrap_text(summary, 450, 11)
            page.insert_text(
                point=(50, 180),
                text=wrapped_text,
                fontsize=11,
                fontname="helv",
                color=(0.2, 0.2, 0.2)
            )
            
        except Exception as e:
            logger.error(f"Error adding creative summary: {e}")
    
    def _add_creative_skills(self, page, skills: List[str]):
        """Add creative professional skills with visual grouping"""
        try:
            # Section header
            page.insert_text(
                point=(50, 250),
                text="CORE SKILLS",
                fontsize=18,
                fontname="helv-b",
                color=(0.2, 0.4, 0.8)
            )
            
            # Skills in columns with bullet points
            y_pos = 275
            for i, skill in enumerate(skills[:20]):
                if y_pos > 750:
                    page = self._add_new_page_if_needed(page)
                    y_pos = 50
                
                page.insert_text(
                    point=(50, y_pos),
                    text=f"• {skill}",
                    fontsize=11,
                    fontname="helv",
                    color=(0.2, 0.2, 0.2)
                )
                y_pos += 15
                
        except Exception as e:
            logger.error(f"Error adding creative skills: {e}")
    
    def _add_creative_experience(self, page, experience: List[Dict[str, Any]]):
        """Add creative professional experience with timeline design"""
        try:
            # Section header
            page.insert_text(
                point=(50, 350),
                text="PROFESSIONAL EXPERIENCE",
                fontsize=18,
                fontname="helv-b",
                color=(0.2, 0.4, 0.8)
            )
            
            y_pos = 375
            for i, exp in enumerate(experience[:5]):
                if y_pos > 750:
                    page = self._add_new_page_if_needed(page)
                    y_pos = 50
                
                # Job title
                if exp.get('title'):
                    page.insert_text(
                        point=(50, y_pos),
                        text=exp['title'],
                        fontsize=13,
                        fontname="helv-b",
                        color=(0.1, 0.1, 0.1)
                    )
                    y_pos += 18
                
                # Company and duration
                company_duration = f"{exp.get('company', '')} | {exp.get('duration', '')}"
                if company_duration.strip() != '|':
                    page.insert_text(
                        point=(50, y_pos),
                        text=company_duration,
                        fontsize=11,
                        fontname="helv",
                        color=(0.4, 0.4, 0.4)
                    )
                    y_pos += 15
                
                # Description
                if exp.get('description'):
                    wrapped_desc = self._wrap_text(exp['description'], 450, 10)
                    page.insert_text(
                        point=(50, y_pos),
                        text=wrapped_desc,
                        fontsize=10,
                        fontname="helv",
                        color=(0.2, 0.2, 0.2)
                    )
                    y_pos += 25
                
                y_pos += 10
                
        except Exception as e:
            logger.error(f"Error adding creative experience: {e}")
    
    def _add_creative_education(self, page, education: List[Dict[str, Any]]):
        """Add creative professional education with modern layout"""
        try:
            # Section header
            page.insert_text(
                point=(50, 500),
                text="EDUCATION",
                fontsize=18,
                fontname="helv-b",
                color=(0.2, 0.4, 0.8)
            )
            
            y_pos = 525
            for edu in education[:3]:
                if y_pos > 750:
                    page = self._add_new_page_if_needed(page)
                    y_pos = 50
                
                # Degree
                if edu.get('degree'):
                    page.insert_text(
                        point=(50, y_pos),
                        text=edu['degree'],
                        fontsize=12,
                        fontname="helv-b",
                        color=(0.1, 0.1, 0.1)
                    )
                    y_pos += 15
                
                # Institution and year
                institution_year = f"{edu.get('institution', '')} | {edu.get('year', '')}"
                if institution_year.strip() != '|':
                    page.insert_text(
                        point=(50, y_pos),
                        text=institution_year,
                        fontsize=10,
                        fontname="helv",
                        color=(0.4, 0.4, 0.4)
                    )
                    y_pos += 20
                
        except Exception as e:
            logger.error(f"Error adding creative education: {e}")
    
    # ===== ACADEMIC/RESEARCH TEMPLATE STYLING =====
    
    def _add_academic_header(self, page, cv_data: Dict[str, Any]):
        """Add academic/research header"""
        try:
            # Name (formal academic style)
            name = cv_data.get('name', 'Academic CV')
            page.insert_text(
                point=(50, 50),
                text=name,
                fontsize=22,
                fontname="helv-b",
                color=(0, 0, 0)
            )
            
            # Academic title
            title = cv_data.get('title', '')
            if title:
                page.insert_text(
                    point=(50, 80),
                    text=title,
                    fontsize=14,
                    fontname="helv",
                    color=(0.2, 0.2, 0.2)
                )
            
            # Contact Information
            contact_info = []
            if cv_data.get('email'):
                contact_info.append(cv_data['email'])
            if cv_data.get('mobile'):
                contact_info.append(cv_data['mobile'])
            if cv_data.get('address'):
                contact_info.append(cv_data['address'])
            
            y_pos = 110
            for contact in contact_info:
                page.insert_text(
                    point=(50, y_pos),
                    text=contact,
                    fontsize=10,
                    fontname="helv",
                    color=(0.4, 0.4, 0.4)
                )
                y_pos += 15
            
        except Exception as e:
            logger.error(f"Error adding academic header: {e}")
    
    def _add_academic_summary(self, page, summary: str):
        """Add academic/research summary"""
        try:
            # Section header
            page.insert_text(
                point=(50, 160),
                text="RESEARCH SUMMARY",
                fontsize=16,
                fontname="helv-b",
                color=(0, 0, 0)
            )
            
            # Summary text
            wrapped_text = self._wrap_text(summary, 450, 11)
            page.insert_text(
                point=(50, 185),
                text=wrapped_text,
                fontsize=11,
                fontname="helv",
                color=(0.2, 0.2, 0.2)
            )
            
        except Exception as e:
            logger.error(f"Error adding academic summary: {e}")
    
    def _add_academic_experience(self, page, experience: List[Dict[str, Any]]):
        """Add academic/research experience"""
        try:
            # Section header
            page.insert_text(
                point=(50, 250),
                text="RESEARCH EXPERIENCE",
                fontsize=16,
                fontname="helv-b",
                color=(0, 0, 0)
            )
            
            y_pos = 275
            for exp in experience[:5]:
                if y_pos > 750:
                    page = self._add_new_page_if_needed(page)
                    y_pos = 50
                
                # Position title
                if exp.get('title'):
                    page.insert_text(
                        point=(50, y_pos),
                        text=exp['title'],
                        fontsize=13,
                        fontname="helv-b",
                        color=(0, 0, 0)
                    )
                    y_pos += 18
                
                # Institution and duration
                institution_duration = f"{exp.get('company', '')} | {exp.get('duration', '')}"
                if institution_duration.strip() != '|':
                    page.insert_text(
                        point=(50, y_pos),
                        text=institution_duration,
                        fontsize=11,
                        fontname="helv",
                        color=(0.4, 0.4, 0.4)
                    )
                    y_pos += 15
                
                # Description
                if exp.get('description'):
                    wrapped_desc = self._wrap_text(exp['description'], 450, 10)
                    page.insert_text(
                        point=(50, y_pos),
                        text=wrapped_desc,
                        fontsize=10,
                        fontname="helv",
                        color=(0.2, 0.2, 0.2)
                    )
                    y_pos += 25
                
                y_pos += 10
                
        except Exception as e:
            logger.error(f"Error adding academic experience: {e}")
    
    def _add_academic_education(self, page, education: List[Dict[str, Any]]):
        """Add academic/research education"""
        try:
            # Section header
            page.insert_text(
                point=(50, 400),
                text="EDUCATION",
                fontsize=16,
                fontname="helv-b",
                color=(0, 0, 0)
            )
            
            y_pos = 425
            for edu in education[:3]:
                if y_pos > 750:
                    page = self._add_new_page_if_needed(page)
                    y_pos = 50
                
                # Degree
                if edu.get('degree'):
                    page.insert_text(
                        point=(50, y_pos),
                        text=edu['degree'],
                        fontsize=12,
                        fontname="helv-b",
                        color=(0, 0, 0)
                    )
                    y_pos += 15
                
                # Institution and year
                institution_year = f"{edu.get('institution', '')} | {edu.get('year', '')}"
                if institution_year.strip() != '|':
                    page.insert_text(
                        point=(50, y_pos),
                        text=institution_year,
                        fontsize=10,
                        fontname="helv",
                        color=(0.4, 0.4, 0.4)
                    )
                    y_pos += 20
                
        except Exception as e:
            logger.error(f"Error adding academic education: {e}")
    
    def _add_academic_publications(self, page, publications: List[str]):
        """Add academic publications section"""
        try:
            # Section header
            page.insert_text(
                point=(50, 500),
                text="PUBLICATIONS",
                fontsize=16,
                fontname="helv-b",
                color=(0, 0, 0)
            )
            
            y_pos = 525
            for pub in publications[:10]:
                if y_pos > 750:
                    page = self._add_new_page_if_needed(page)
                    y_pos = 50
                
                page.insert_text(
                    point=(50, y_pos),
                    text=f"• {pub}",
                    fontsize=10,
                    fontname="helv",
                    color=(0.2, 0.2, 0.2)
                )
                y_pos += 15
                
        except Exception as e:
            logger.error(f"Error adding academic publications: {e}")
    
    # ===== EXECUTIVE/LEADERSHIP TEMPLATE STYLING =====
    
    def _add_executive_header(self, page, cv_data: Dict[str, Any]):
        """Add executive/leadership header"""
        try:
            # Name (executive style)
            name = cv_data.get('name', 'Executive CV')
            page.insert_text(
                point=(50, 50),
                text=name.upper(),
                fontsize=26,
                fontname="helv-b",
                color=(0, 0, 0)
            )
            
            # Executive title
            title = cv_data.get('title', '')
            if title:
                page.insert_text(
                    point=(50, 85),
                    text=title,
                    fontsize=16,
                    fontname="helv",
                    color=(0.3, 0.3, 0.3)
                )
            
            # Executive contact
            contact_info = []
            if cv_data.get('email'):
                contact_info.append(cv_data['email'])
            if cv_data.get('mobile'):
                contact_info.append(cv_data['mobile'])
            if cv_data.get('linkedin'):
                contact_info.append(f"LinkedIn: {cv_data['linkedin']}")
            
            y_pos = 50
            for contact in contact_info:
                page.insert_text(
                    point=(400, y_pos),
                    text=contact,
                    fontsize=11,
                    fontname="helv",
                    color=(0.4, 0.4, 0.4)
                )
                y_pos += 18
            
        except Exception as e:
            logger.error(f"Error adding executive header: {e}")
    
    def _add_executive_summary(self, page, summary: str):
        """Add executive/leadership summary"""
        try:
            # Section header
            page.insert_text(
                point=(50, 130),
                text="EXECUTIVE SUMMARY",
                fontsize=18,
                fontname="helv-b",
                color=(0, 0, 0)
            )
            
            # Summary text
            wrapped_text = self._wrap_text(summary, 450, 11)
            page.insert_text(
                point=(50, 155),
                text=wrapped_text,
                fontsize=11,
                fontname="helv",
                color=(0.2, 0.2, 0.2)
            )
            
        except Exception as e:
            logger.error(f"Error adding executive summary: {e}")
    
    def _add_executive_experience(self, page, experience: List[Dict[str, Any]]):
        """Add executive/leadership experience"""
        try:
            # Section header
            page.insert_text(
                point=(50, 220),
                text="LEADERSHIP EXPERIENCE",
                fontsize=18,
                fontname="helv-b",
                color=(0, 0, 0)
            )
            
            y_pos = 245
            for exp in experience[:5]:
                if y_pos > 750:
                    page = self._add_new_page_if_needed(page)
                    y_pos = 50
                
                # Position title
                if exp.get('title'):
                    page.insert_text(
                        point=(50, y_pos),
                        text=exp['title'],
                        fontsize=14,
                        fontname="helv-b",
                        color=(0, 0, 0)
                    )
                    y_pos += 18
                
                # Company and duration
                company_duration = f"{exp.get('company', '')} | {exp.get('duration', '')}"
                if company_duration.strip() != '|':
                    page.insert_text(
                        point=(50, y_pos),
                        text=company_duration,
                        fontsize=11,
                        fontname="helv",
                        color=(0.4, 0.4, 0.4)
                    )
                    y_pos += 15
                
                # Description
                if exp.get('description'):
                    wrapped_desc = self._wrap_text(exp['description'], 450, 10)
                    page.insert_text(
                        point=(50, y_pos),
                        text=wrapped_desc,
                        fontsize=10,
                        fontname="helv",
                        color=(0.2, 0.2, 0.2)
                    )
                    y_pos += 25
                
                y_pos += 10
                
        except Exception as e:
            logger.error(f"Error adding executive experience: {e}")
    
    def _add_executive_education(self, page, education: List[Dict[str, Any]]):
        """Add executive/leadership education"""
        try:
            # Section header
            page.insert_text(
                point=(50, 400),
                text="EDUCATION",
                fontsize=18,
                fontname="helv-b",
                color=(0, 0, 0)
            )
            
            y_pos = 425
            for edu in education[:3]:
                if y_pos > 750:
                    page = self._add_new_page_if_needed(page)
                    y_pos = 50
                
                # Degree
                if edu.get('degree'):
                    page.insert_text(
                        point=(50, y_pos),
                        text=edu['degree'],
                        fontsize=12,
                        fontname="helv-b",
                        color=(0, 0, 0)
                    )
                    y_pos += 15
                
                # Institution and year
                institution_year = f"{edu.get('institution', '')} | {edu.get('year', '')}"
                if institution_year.strip() != '|':
                    page.insert_text(
                        point=(50, y_pos),
                        text=institution_year,
                        fontsize=10,
                        fontname="helv",
                        color=(0.4, 0.4, 0.4)
                    )
                    y_pos += 20
                
        except Exception as e:
            logger.error(f"Error adding executive education: {e}")
    
    def _add_executive_leadership(self, page, leadership: List[Dict[str, Any]]):
        """Add executive/leadership positions"""
        try:
            # Section header
            page.insert_text(
                point=(50, 500),
                text="BOARD POSITIONS & LEADERSHIP",
                fontsize=18,
                fontname="helv-b",
                color=(0, 0, 0)
            )
            
            y_pos = 525
            for pos in leadership[:5]:
                if y_pos > 750:
                    page = self._add_new_page_if_needed(page)
                    y_pos = 50
                
                # Position
                if pos.get('title'):
                    page.insert_text(
                        point=(50, y_pos),
                        text=pos['title'],
                        fontsize=12,
                        fontname="helv-b",
                        color=(0, 0, 0)
                    )
                    y_pos += 15
                
                # Organization and duration
                org_duration = f"{pos.get('organization', '')} | {pos.get('duration', '')}"
                if org_duration.strip() != '|':
                    page.insert_text(
                        point=(50, y_pos),
                        text=org_duration,
                        fontsize=10,
                        fontname="helv",
                        color=(0.4, 0.4, 0.4)
                    )
                    y_pos += 20
                
        except Exception as e:
            logger.error(f"Error adding executive leadership: {e}")
    
    # ===== UTILITY FUNCTIONS =====
    
    def _wrap_text(self, text: str, max_width: int, font_size: int) -> str:
        """Simple text wrapping for PDF generation"""
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
    
    def _add_new_page_if_needed(self, current_page):
        """Add a new page if needed and return the new page"""
        try:
            doc = current_page.parent
            new_page = doc.new_page(width=595, height=842)  # A4 size
            return new_page
        except Exception as e:
            logger.error(f"Error adding new page: {e}")
            return current_page
