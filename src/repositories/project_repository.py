from typing import List, Optional

from sqlalchemy.orm import Session

from src.models.database import Project


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, project: Project) -> Project:
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def find_by_id(self, project_id: int) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def find_by_user(self, user_id: int) -> List[Project]:
        return (
            self.db.query(Project)
            .filter(Project.user_id == user_id)
            .order_by(Project.updated_at.desc())
            .all()
        )

    def find_all(self) -> List[Project]:
        return self.db.query(Project).all()

    def update(self, project: Project) -> Project:
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project_id: int) -> bool:
        project = self.find_by_id(project_id)
        if project:
            self.db.delete(project)
            self.db.commit()
            return True
        return False
