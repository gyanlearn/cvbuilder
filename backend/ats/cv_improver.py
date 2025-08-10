import logging
import fitz  # PyMuPDF
import google.generativeai as genai
from typing import Dict, Any, List, Tuple, Optional
import tempfile
import os
from datetime import datetime

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
        
    def improve_cv(self, original_cv_text: str, ats_feedback: Dict[str, Any], 
                   industry: str, original_score: int) -> Dict[str, Any]:
        """
        Improve CV based on ATS score and feedback
        
        Args:
            original_cv_text: Original CV text
            ats_feedback: ATS analysis results
            industry: Target industry
            original_score: Original ATS score
            
        Returns:
            Dict containing improved CV text, new score, and PDF path
        """
        try:
            # Determine improvement strategy based on ATS score
            strategy = self._determine_strategy(original_score)
            logger.info(f"Using {strategy} strategy for CV improvement (score: {original_score})")
            
            # Generate improvement prompt
            prompt = self._create_improvement_prompt(original_cv_text, ats_feedback, strategy)
            
            # Get improved CV text from Gemini
            improved_cv_text = self._get_improved_cv(prompt)
            
            if not improved_cv_text:
                logger.error("Failed to get improved CV text from Gemini")
                return self._create_error_response("Failed to improve CV text")
            
            # Generate PDF based on strategy
            pdf_path = self._generate_pdf(improved_cv_text, strategy, original_cv_text)
            
            if not pdf_path:
                logger.error("Failed to generate PDF")
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
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error improving CV: {e}")
            return self._create_error_response(str(e))
    
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
            # Create PDF filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"improved_cv_{strategy}_{timestamp}.pdf"
            pdf_path = os.path.join(self.temp_dir, pdf_filename)
            
            # Create PDF document
            doc = fitz.open()
            
            if strategy == "minor_fix":
                # Preserve original layout style
                page = doc.new_page(width=595, height=842)  # A4 size
                self._add_text_to_page(page, improved_cv_text, preserve_style=True)
                
            elif strategy == "major_overhaul":
                # Clean, modern ATS-friendly layout
                page = doc.new_page(width=595, height=842)
                self._add_text_to_page(page, improved_cv_text, preserve_style=False)
                
            else:  # hybrid
                # Balance between original and optimized
                page = doc.new_page(width=595, height=842)
                self._add_text_to_page(page, improved_cv_text, preserve_style=True)
            
            # Save PDF
            doc.save(pdf_path)
            doc.close()
            
            logger.info(f"PDF generated successfully: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return None
    
    def _add_text_to_page(self, page, text: str, preserve_style: bool = True):
        """Add text to PDF page with appropriate formatting"""
        try:
            # Split text into sections
            sections = self._parse_cv_sections(text)
            
            y_position = 50  # Start position from top
            left_margin = 50
            right_margin = 545
            
            # Add title
            if sections.get('header'):
                page.insert_text(
                    point=(left_margin, y_position),
                    text=sections['header'],
                    fontsize=18,
                    fontname="helv-b",
                    color=(0, 0, 0)
                )
                y_position += 30
            
            # Add contact info
            if sections.get('contact'):
                page.insert_text(
                    point=(left_margin, y_position),
                    text=sections['contact'],
                    fontsize=10,
                    fontname="helv",
                    color=(0, 0, 0)
                )
                y_position += 20
            
            # Add summary
            if sections.get('summary'):
                page.insert_text(
                    point=(left_margin, y_position),
                    text="PROFESSIONAL SUMMARY",
                    fontsize=14,
                    fontname="helv-b",
                    color=(0, 0, 0)
                )
                y_position += 20
                
                # Wrap text to fit page width
                wrapped_text = self._wrap_text(sections['summary'], right_margin - left_margin, 10)
                page.insert_text(
                    point=(left_margin, y_position),
                    text=wrapped_text,
                    fontsize=10,
                    fontname="helv",
                    color=(0, 0, 0)
                )
                y_position += 30
            
            # Add skills
            if sections.get('skills'):
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
            
            # Add experience
            if sections.get('experience'):
                page.insert_text(
                    point=(left_margin, y_position),
                    text="PROFESSIONAL EXPERIENCE",
                    fontsize=14,
                    fontname="helv-b",
                    color=(0, 0, 0)
                )
                y_position += 20
                
                for exp in sections['experience']:
                    if y_position > 750:  # Check if we need a new page
                        page = self._add_new_page_if_needed(page)
                        y_position = 50
                    
                    # Company and title
                    company_title = f"{exp.get('company', '')} - {exp.get('title', '')}"
                    page.insert_text(
                        point=(left_margin, y_position),
                        text=company_title,
                        fontsize=12,
                        fontname="helv-b",
                        color=(0, 0, 0)
                    )
                    y_position += 15
                    
                    # Duration
                    if exp.get('duration'):
                        page.insert_text(
                            point=(left_margin, y_position),
                            text=exp['duration'],
                            fontsize=10,
                            fontname="helv",
                            color=(0.5, 0.5, 0.5)
                        )
                        y_position += 15
                    
                    # Description
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
                    
                    y_position += 10
            
            # Add education
            if sections.get('education'):
                if y_position > 750:
                    page = self._add_new_page_if_needed(page)
                    y_position = 50
                
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
                        page = self._add_new_page_if_needed(page)
                        y_position = 50
                    
                    edu_text = f"{edu.get('degree', '')} - {edu.get('institution', '')}"
                    page.insert_text(
                        point=(left_margin, y_position),
                        text=edu_text,
                        fontsize=10,
                        fontname="helv",
                        color=(0, 0, 0)
                    )
                    y_position += 15
                    
                    if edu.get('year'):
                        page.insert_text(
                            point=(left_margin, y_position),
                            text=edu['year'],
                            fontsize=10,
                            fontname="helv",
                            color=(0.5, 0.5, 0.5)
                        )
                        y_position += 20
                    else:
                        y_position += 5
            
        except Exception as e:
            logger.error(f"Error adding text to page: {e}")
            raise
    
    def _add_new_page_if_needed(self, current_page):
        """Add a new page if needed and return it"""
        doc = current_page.parent
        new_page = doc.new_page(width=595, height=842)
        return new_page
    
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
