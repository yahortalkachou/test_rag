import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: python-docx not installed. DOCX support disabled.")

class InnoStandardPraser:
 
    def _file_check(self, file_path: str):
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx is not installed. Install it with: pip install python-docx")
        
        if not Path(file_path).exists():
            raise FileNotFoundError(f"DOCX file not found: {file_path}")
    
    def _get_instance_between_keywords (self, lst: List[str], begin: str, end: str) -> List[str]:
        try:
            start = lst.index(begin) + 1
        except Exception as e:
            return []
        try:
            stop = lst.index(end)
            return lst[start:stop]
        except Exception as e:
            return lst[start:]
    
    def _get_innowise_project_from_table (self, cells: List)->Dict:
        descriprion = cells[1].text
        project_name = cells[0].text.split('\n')
        summury = project_name[1]
        project_name = project_name[0]
        roles = self._get_instance_between_keywords(descriprion.split('\n'),"Project roles","Period")[0].split('/')
        descriprion = summury + descriprion
        
        return {
            "name": project_name,
            "description": descriprion,
            "roles" : roles,
            "CV_id" : "L1"
        }
                 
    def parse_inniwise_std (self, file_path) -> Dict[str,any]:
        """
        Extract personal and project data from .docx innowise standard file.
        
        Args:
            file_path: Path to .docx file
            
        Returns:
            Extracted text as string
        """
        self._file_check(file_path)
        name = ""
        roles = []
        eduction = ""
        languages = []
        domains = []
        personal_data = ""
        projects = []
        level = ""
        
        para_texts = []
        
        try:
            doc = Document(file_path)
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    para_texts.append(paragraph.text)
            if len(para_texts) == 3:
                name = para_texts[0]
                level = para_texts[1].split(" ")[0]
                roles = para_texts[1].split("/")
                roles[0] = " ".join(roles[0].split(" ")[1:])
            #print(name,level, roles)
                            
            # Extract from std tables
            if len(doc.tables) == 3:
                #pesonal/global metadat
                about = doc.tables[0].rows[0].cells[0].text
                about = about.split('\n')
                #print (about)
                eduction = self._get_instance_between_keywords(about,"Education","Language proficiency")
                languages = self._get_instance_between_keywords(about,"Language proficiency","Domains")
                domains = self._get_instance_between_keywords(about,"Domains","Certificates")
                cert = self._get_instance_between_keywords(about,"Certificates","axaxaxax")
                #print (f"ed: {eduction} dom: {domains} langs: {languages} certs: {cert}")
                description = doc.tables[0].rows[0].cells[1].text.split('\n')[1]
                #print(f"description\n{description}")
                #projectdata section
                
                if len(doc.tables) == 3:
                    table = doc.tables[1]
                    for row in table.rows[1:]:
                        projects.append(self._get_innowise_project_from_table(row.cells))
                
            self.global_data = {
                "CV_id": "L1",
                "name": name,
                "level": level,
                "roles": roles,
                "education": eduction,
                "languages": languages,
                "domains": domains,
                "projects": projects,
                "description": description
            }
            return self.global_data
        
        except Exception as e:
            raise Exception(f"Error reading DOCX file: {e}")
    
    def get_personal_data (self):
        return {
            "name": self.global_data["name"],
            "level": self.global_data["level"],
            "roles": self.global_data["roles"],
            "education": self.global_data["education"],
            "languages": self.global_data["languages"],
            "domains": self.global_data["domains"],
            "projects": self.global_data["projects"],
            "description": self.global_data["description"]
        }
    
    def get_projects_data (self):
        return self.global_data["projects"]
    



if __name__ == "__main__":
    parser = InnoStandardPraser()
    try:
        parser.parse_inniwise_std("cv_lev.docx")
    except Exception as e:
        print(f"DOCX parsing error: {e}")
    
