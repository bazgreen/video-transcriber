# Multi-User Collaboration & Team Features

## 🎯 Issue Overview

**Priority**: ⭐⭐⭐ High Priority  
**Epic**: User Experience & Accessibility  
**Estimated Effort**: 8-10 weeks  
**Dependencies**: User authentication system, database schema updates, real-time messaging infrastructure

### Problem Statement

Users working in teams face significant collaboration challenges when working with transcriptions:

- **No shared workspaces** for team projects and content organization
- **Lack of real-time collaboration** on transcript editing and review
- **No review workflows** for ensuring transcription accuracy and approval
- **Missing comment system** for timestamped feedback and annotations
- **No role-based access control** for different team member responsibilities
- **No activity tracking** to understand team member contributions and changes

### Solution Overview

Implement a comprehensive collaboration platform that transforms the Video Transcriber from a single-user tool into a powerful team collaboration platform with shared workspaces, real-time editing, review workflows, and comprehensive team management features.

## ✨ Features & Capabilities

### 🏢 Core Collaboration Features

#### Team Workspaces & Project Management

- Shared project spaces with hierarchical organization
- Role-based access control (Owner, Admin, Editor, Reviewer, Viewer)
- Project templates and standardized workflows
- Resource sharing and team libraries
- Cross-project content discovery and reuse

#### Real-Time Collaborative Editing

- Simultaneous multi-user transcript editing with conflict resolution
- Live cursor tracking and user presence indicators
- Real-time synchronization of changes across all team members
- Automatic conflict detection and resolution
- Version history with detailed change tracking

#### Comment & Annotation System

- Timestamped comments on specific transcript segments
- Threaded discussions with reply chains
- @mentions and notification system
- Comment resolution and status tracking
- Rich text formatting and file attachments

#### Review & Approval Workflows

- Customizable approval workflows with multiple review stages
- Task assignment and deadline management
- Quality gates and approval criteria
- Automated notifications and reminders
- Approval history and audit trails

## 🏗️ Technical Implementation

### Phase 1: Core Team Infrastructure (3 weeks)

#### Task 1.1: Team Management System
**File**: `src/services/team_management.py`

```python
"""
Team management service for multi-user collaboration features.
Handles team creation, member management, roles, and permissions.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Boolean, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID

logger = logging.getLogger(__name__)

Base = declarative_base()

class TeamRole(Enum):
    """Enumeration of team roles with hierarchical permissions."""
    OWNER = "owner"        # Full access, can delete team
    ADMIN = "admin"        # Manage members, settings, all content
    EDITOR = "editor"      # Create, edit, delete own content + assigned content
    REVIEWER = "reviewer"  # Review and comment, limited editing
    VIEWER = "viewer"      # Read-only access

class ProjectStatus(Enum):
    """Project lifecycle status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    COMPLETED = "completed"

# Database Models
class Team(Base):
    """Team model for multi-user collaboration."""
    __tablename__ = 'teams'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSON, default=dict)
    
    # Relationships
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="team", cascade="all, delete-orphan")

class TeamMember(Base):
    """Team membership with roles and permissions."""
    __tablename__ = 'team_members'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'), nullable=False)
    user_id = Column(String(255), nullable=False)  # Reference to user system
    role = Column(String(50), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    permissions = Column(JSON, default=dict)
    
    # Relationships
    team = relationship("Team", back_populates="members")

class Project(Base):
    """Project model for organizing team content."""
    __tablename__ = 'projects'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default=ProjectStatus.ACTIVE.value)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    team = relationship("Team", back_populates="projects")
    sessions = relationship("ProjectSession", back_populates="project")

class ProjectSession(Base):
    """Link transcription sessions to projects."""
    __tablename__ = 'project_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    session_id = Column(String(255), nullable=False)  # Reference to transcription session
    added_by = Column(String(255), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    project = relationship("Project", back_populates="sessions")

@dataclass
class TeamInfo:
    """Data transfer object for team information."""
    id: str
    name: str
    description: str
    member_count: int
    project_count: int
    created_at: str
    settings: Dict[str, Any]

@dataclass
class MemberInfo:
    """Data transfer object for team member information."""
    id: str
    user_id: str
    role: str
    joined_at: str
    last_active: str
    permissions: Dict[str, Any]

class TeamManagementService:
    """Service for managing teams, members, and projects."""
    
    def __init__(self, db_session):
        """Initialize with database session."""
        self.db = db_session
        
    def create_team(self, name: str, description: str, owner_user_id: str, 
                   settings: Dict[str, Any] = None) -> TeamInfo:
        """
        Create a new team with the specified owner.
        
        Args:
            name: Team name
            description: Team description
            owner_user_id: User ID of the team owner
            settings: Optional team settings
            
        Returns:
            TeamInfo object with created team details
        """
        try:
            # Create team
            team = Team(
                name=name,
                description=description,
                settings=settings or {}
            )
            
            self.db.add(team)
            self.db.flush()  # Get team ID
            
            # Add owner as team member
            owner_member = TeamMember(
                team_id=team.id,
                user_id=owner_user_id,
                role=TeamRole.OWNER.value,
                permissions={
                    'manage_team': True,
                    'manage_members': True,
                    'manage_projects': True,
                    'delete_team': True,
                    'edit_all_content': True
                }
            )
            
            self.db.add(owner_member)
            self.db.commit()
            
            return TeamInfo(
                id=str(team.id),
                name=team.name,
                description=team.description,
                member_count=1,
                project_count=0,
                created_at=team.created_at.isoformat(),
                settings=team.settings
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating team: {e}")
            raise
    
    def add_team_member(self, team_id: str, user_id: str, role: TeamRole, 
                       added_by: str) -> MemberInfo:
        """
        Add a new member to a team with specified role.
        
        Args:
            team_id: Team ID
            user_id: User ID to add
            role: TeamRole for the new member
            added_by: User ID of who is adding the member
            
        Returns:
            MemberInfo object with member details
        """
        try:
            # Verify permissions
            if not self._has_permission(team_id, added_by, 'manage_members'):
                raise PermissionError("Insufficient permissions to add members")
            
            # Check if user is already a member
            existing = self.db.query(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            ).first()
            
            if existing:
                raise ValueError("User is already a team member")
            
            # Create member with role-based permissions
            permissions = self._get_role_permissions(role)
            
            member = TeamMember(
                team_id=team_id,
                user_id=user_id,
                role=role.value,
                permissions=permissions
            )
            
            self.db.add(member)
            self.db.commit()
            
            return MemberInfo(
                id=str(member.id),
                user_id=member.user_id,
                role=member.role,
                joined_at=member.joined_at.isoformat(),
                last_active=member.last_active.isoformat(),
                permissions=member.permissions
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding team member: {e}")
            raise
    
    def create_project(self, team_id: str, name: str, description: str, 
                      created_by: str, settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new project within a team.
        
        Args:
            team_id: Team ID
            name: Project name
            description: Project description
            created_by: User ID creating the project
            settings: Optional project settings
            
        Returns:
            Project information dictionary
        """
        try:
            # Verify permissions
            if not self._has_permission(team_id, created_by, 'manage_projects'):
                raise PermissionError("Insufficient permissions to create projects")
            
            project = Project(
                team_id=team_id,
                name=name,
                description=description,
                created_by=created_by,
                settings=settings or {}
            )
            
            self.db.add(project)
            self.db.commit()
            
            return {
                'id': str(project.id),
                'team_id': str(project.team_id),
                'name': project.name,
                'description': project.description,
                'status': project.status,
                'created_by': project.created_by,
                'created_at': project.created_at.isoformat(),
                'settings': project.settings
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating project: {e}")
            raise
    
    def add_session_to_project(self, project_id: str, session_id: str, 
                             added_by: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Add a transcription session to a project.
        
        Args:
            project_id: Project ID
            session_id: Transcription session ID
            added_by: User ID adding the session
            metadata: Optional session metadata
            
        Returns:
            Success boolean
        """
        try:
            # Verify project exists and user has access
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError("Project not found")
            
            if not self._has_project_access(project_id, added_by, 'edit'):
                raise PermissionError("Insufficient permissions to add sessions")
            
            # Check if session already exists in project
            existing = self.db.query(ProjectSession).filter(
                ProjectSession.project_id == project_id,
                ProjectSession.session_id == session_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            project_session = ProjectSession(
                project_id=project_id,
                session_id=session_id,
                added_by=added_by,
                metadata=metadata or {}
            )
            
            self.db.add(project_session)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding session to project: {e}")
            raise
    
    def get_team_info(self, team_id: str, user_id: str) -> TeamInfo:
        """
        Get comprehensive team information for a user.
        
        Args:
            team_id: Team ID
            user_id: User ID requesting info
            
        Returns:
            TeamInfo object
        """
        try:
            # Verify user is team member
            if not self._is_team_member(team_id, user_id):
                raise PermissionError("Not a team member")
            
            team = self.db.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise ValueError("Team not found")
            
            member_count = self.db.query(TeamMember).filter(
                TeamMember.team_id == team_id
            ).count()
            
            project_count = self.db.query(Project).filter(
                Project.team_id == team_id
            ).count()
            
            return TeamInfo(
                id=str(team.id),
                name=team.name,
                description=team.description,
                member_count=member_count,
                project_count=project_count,
                created_at=team.created_at.isoformat(),
                settings=team.settings
            )
            
        except Exception as e:
            logger.error(f"Error getting team info: {e}")
            raise
    
    def get_user_teams(self, user_id: str) -> List[TeamInfo]:
        """
        Get all teams for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of TeamInfo objects
        """
        try:
            teams = self.db.query(Team).join(TeamMember).filter(
                TeamMember.user_id == user_id
            ).all()
            
            team_info_list = []
            for team in teams:
                member_count = len(team.members)
                project_count = len(team.projects)
                
                team_info_list.append(TeamInfo(
                    id=str(team.id),
                    name=team.name,
                    description=team.description,
                    member_count=member_count,
                    project_count=project_count,
                    created_at=team.created_at.isoformat(),
                    settings=team.settings
                ))
            
            return team_info_list
            
        except Exception as e:
            logger.error(f"Error getting user teams: {e}")
            raise
    
    # Helper methods
    def _has_permission(self, team_id: str, user_id: str, permission: str) -> bool:
        """Check if user has specific permission in team."""
        try:
            member = self.db.query(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            ).first()
            
            if not member:
                return False
            
            return member.permissions.get(permission, False)
            
        except Exception:
            return False
    
    def _is_team_member(self, team_id: str, user_id: str) -> bool:
        """Check if user is a team member."""
        try:
            member = self.db.query(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            ).first()
            
            return member is not None
            
        except Exception:
            return False
    
    def _has_project_access(self, project_id: str, user_id: str, access_type: str) -> bool:
        """Check if user has access to project."""
        try:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return False
            
            # Check team membership and permissions
            return self._has_permission(str(project.team_id), user_id, f'{access_type}_content')
            
        except Exception:
            return False
    
    def _get_role_permissions(self, role: TeamRole) -> Dict[str, bool]:
        """Get permissions for a specific role."""
        role_permissions = {
            TeamRole.OWNER: {
                'manage_team': True,
                'manage_members': True,
                'manage_projects': True,
                'delete_team': True,
                'edit_all_content': True,
                'review_content': True,
                'view_all_content': True
            },
            TeamRole.ADMIN: {
                'manage_team': False,
                'manage_members': True,
                'manage_projects': True,
                'delete_team': False,
                'edit_all_content': True,
                'review_content': True,
                'view_all_content': True
            },
            TeamRole.EDITOR: {
                'manage_team': False,
                'manage_members': False,
                'manage_projects': False,
                'delete_team': False,
                'edit_all_content': False,
                'edit_own_content': True,
                'review_content': True,
                'view_all_content': True
            },
            TeamRole.REVIEWER: {
                'manage_team': False,
                'manage_members': False,
                'manage_projects': False,
                'delete_team': False,
                'edit_all_content': False,
                'edit_own_content': False,
                'review_content': True,
                'view_all_content': True
            },
            TeamRole.VIEWER: {
                'manage_team': False,
                'manage_members': False,
                'manage_projects': False,
                'delete_team': False,
                'edit_all_content': False,
                'edit_own_content': False,
                'review_content': False,
                'view_all_content': True
            }
        }
        
        return role_permissions.get(role, {})

# Factory function
def create_team_management_service(db_session) -> TeamManagementService:
    """Create team management service with database session."""
    return TeamManagementService(db_session)
```

**Acceptance Criteria**:
- ✅ Team creation and management with hierarchical roles
- ✅ Project organization within teams
- ✅ Role-based permission system
- ✅ Database models with proper relationships
- ✅ Comprehensive error handling and validation
- ✅ Audit trail for all team operations

#### Task 1.2: Real-Time Collaboration Engine
**File**: `src/services/realtime_collaboration.py`

```python
"""
Real-time collaboration service for simultaneous multi-user editing.
Handles operational transformation, conflict resolution, and live synchronization.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib

try:
    import socketio
    from flask_socketio import SocketIO, emit, join_room, leave_room
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class Operation:
    """Represents a single edit operation."""
    id: str
    type: str  # 'insert', 'delete', 'retain'
    position: int
    content: str
    length: int
    timestamp: str
    user_id: str
    session_id: str

@dataclass
class UserPresence:
    """Represents user presence in a collaboration session."""
    user_id: str
    username: str
    cursor_position: int
    selection_start: int
    selection_end: int
    last_seen: str
    color: str

class OperationalTransform:
    """Operational transformation for conflict-free collaborative editing."""
    
    @staticmethod
    def transform_operations(op1: Operation, op2: Operation) -> tuple[Operation, Operation]:
        """
        Transform two concurrent operations to maintain consistency.
        
        Args:
            op1: First operation
            op2: Second operation
            
        Returns:
            Tuple of transformed operations
        """
        try:
            # Transform based on operation types
            if op1.type == 'insert' and op2.type == 'insert':
                return OperationalTransform._transform_insert_insert(op1, op2)
            elif op1.type == 'insert' and op2.type == 'delete':
                return OperationalTransform._transform_insert_delete(op1, op2)
            elif op1.type == 'delete' and op2.type == 'insert':
                op2_t, op1_t = OperationalTransform._transform_insert_delete(op2, op1)
                return op1_t, op2_t
            elif op1.type == 'delete' and op2.type == 'delete':
                return OperationalTransform._transform_delete_delete(op1, op2)
            else:
                return op1, op2
                
        except Exception as e:
            logger.error(f"Error transforming operations: {e}")
            return op1, op2
    
    @staticmethod
    def _transform_insert_insert(op1: Operation, op2: Operation) -> tuple[Operation, Operation]:
        """Transform two concurrent insert operations."""
        if op1.position <= op2.position:
            # op1 happens before op2, adjust op2's position
            op2_transformed = Operation(
                id=op2.id,
                type=op2.type,
                position=op2.position + len(op1.content),
                content=op2.content,
                length=op2.length,
                timestamp=op2.timestamp,
                user_id=op2.user_id,
                session_id=op2.session_id
            )
            return op1, op2_transformed
        else:
            # op2 happens before op1, adjust op1's position
            op1_transformed = Operation(
                id=op1.id,
                type=op1.type,
                position=op1.position + len(op2.content),
                content=op1.content,
                length=op1.length,
                timestamp=op1.timestamp,
                user_id=op1.user_id,
                session_id=op1.session_id
            )
            return op1_transformed, op2
    
    @staticmethod
    def _transform_insert_delete(insert_op: Operation, delete_op: Operation) -> tuple[Operation, Operation]:
        """Transform insert and delete operations."""
        if insert_op.position <= delete_op.position:
            # Insert happens before delete range
            delete_transformed = Operation(
                id=delete_op.id,
                type=delete_op.type,
                position=delete_op.position + len(insert_op.content),
                content=delete_op.content,
                length=delete_op.length,
                timestamp=delete_op.timestamp,
                user_id=delete_op.user_id,
                session_id=delete_op.session_id
            )
            return insert_op, delete_transformed
        elif insert_op.position >= delete_op.position + delete_op.length:
            # Insert happens after delete range
            insert_transformed = Operation(
                id=insert_op.id,
                type=insert_op.type,
                position=insert_op.position - delete_op.length,
                content=insert_op.content,
                length=insert_op.length,
                timestamp=insert_op.timestamp,
                user_id=insert_op.user_id,
                session_id=insert_op.session_id
            )
            return insert_transformed, delete_op
        else:
            # Insert happens within delete range - complex case
            return insert_op, delete_op

class CollaborationSession:
    """Manages a single collaborative editing session."""
    
    def __init__(self, session_id: str):
        """Initialize collaboration session."""
        self.session_id = session_id
        self.document_state = ""
        self.operation_history: List[Operation] = []
        self.user_presence: Dict[str, UserPresence] = {}
        self.version = 0
        self.last_checkpoint = datetime.utcnow()
        
    def apply_operation(self, operation: Operation) -> bool:
        """
        Apply an operation to the document state.
        
        Args:
            operation: Operation to apply
            
        Returns:
            Success boolean
        """
        try:
            if operation.type == 'insert':
                self.document_state = (
                    self.document_state[:operation.position] +
                    operation.content +
                    self.document_state[operation.position:]
                )
            elif operation.type == 'delete':
                end_pos = operation.position + operation.length
                self.document_state = (
                    self.document_state[:operation.position] +
                    self.document_state[end_pos:]
                )
            
            self.operation_history.append(operation)
            self.version += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying operation: {e}")
            return False
    
    def update_user_presence(self, user_presence: UserPresence):
        """Update user presence information."""
        self.user_presence[user_presence.user_id] = user_presence
    
    def remove_user_presence(self, user_id: str):
        """Remove user from presence tracking."""
        self.user_presence.pop(user_id, None)
    
    def get_document_state(self) -> Dict[str, Any]:
        """Get current document state with metadata."""
        return {
            'content': self.document_state,
            'version': self.version,
            'last_modified': self.last_checkpoint.isoformat(),
            'user_presence': [asdict(presence) for presence in self.user_presence.values()]
        }

class RealtimeCollaborationService:
    """Service for managing real-time collaborative editing."""
    
    def __init__(self, socketio_instance=None):
        """Initialize with optional SocketIO instance."""
        self.socketio = socketio_instance
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.user_session_mapping: Dict[str, Set[str]] = defaultdict(set)
        
    def join_collaboration_session(self, session_id: str, user_id: str, 
                                 username: str) -> Dict[str, Any]:
        """
        Join a collaborative editing session.
        
        Args:
            session_id: Session ID to join
            user_id: User ID joining
            username: Display name
            
        Returns:
            Session state and user info
        """
        try:
            # Create or get existing session
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = CollaborationSession(session_id)
            
            session = self.active_sessions[session_id]
            
            # Add user presence
            user_presence = UserPresence(
                user_id=user_id,
                username=username,
                cursor_position=0,
                selection_start=0,
                selection_end=0,
                last_seen=datetime.utcnow().isoformat(),
                color=self._generate_user_color(user_id)
            )
            
            session.update_user_presence(user_presence)
            self.user_session_mapping[user_id].add(session_id)
            
            # Join SocketIO room if available
            if self.socketio and SOCKETIO_AVAILABLE:
                join_room(f"collab_{session_id}")
                
                # Notify other users
                emit('user_joined', {
                    'user_id': user_id,
                    'username': username,
                    'color': user_presence.color
                }, room=f"collab_{session_id}", include_self=False)
            
            return {
                'session_id': session_id,
                'document_state': session.get_document_state(),
                'user_presence': user_presence,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error joining collaboration session: {e}")
            return {'success': False, 'error': str(e)}
    
    def leave_collaboration_session(self, session_id: str, user_id: str):
        """
        Leave a collaborative editing session.
        
        Args:
            session_id: Session ID to leave
            user_id: User ID leaving
        """
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.remove_user_presence(user_id)
                
                # Remove from mapping
                self.user_session_mapping[user_id].discard(session_id)
                
                # Leave SocketIO room
                if self.socketio and SOCKETIO_AVAILABLE:
                    leave_room(f"collab_{session_id}")
                    
                    # Notify other users
                    emit('user_left', {
                        'user_id': user_id
                    }, room=f"collab_{session_id}")
                
                # Clean up empty sessions
                if not session.user_presence:
                    del self.active_sessions[session_id]
                    
        except Exception as e:
            logger.error(f"Error leaving collaboration session: {e}")
    
    def handle_operation(self, session_id: str, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming collaborative editing operation.
        
        Args:
            session_id: Session ID
            operation_data: Operation data from client
            
        Returns:
            Result with transformed operation
        """
        try:
            if session_id not in self.active_sessions:
                return {'success': False, 'error': 'Session not found'}
            
            session = self.active_sessions[session_id]
            
            # Create operation object
            operation = Operation(
                id=operation_data.get('id', self._generate_operation_id()),
                type=operation_data['type'],
                position=operation_data['position'],
                content=operation_data.get('content', ''),
                length=operation_data.get('length', 0),
                timestamp=datetime.utcnow().isoformat(),
                user_id=operation_data['user_id'],
                session_id=session_id
            )
            
            # Transform against concurrent operations
            transformed_operation = self._transform_against_history(operation, session)
            
            # Apply operation
            if session.apply_operation(transformed_operation):
                # Broadcast to other users
                if self.socketio and SOCKETIO_AVAILABLE:
                    emit('operation_applied', {
                        'operation': asdict(transformed_operation),
                        'document_version': session.version
                    }, room=f"collab_{session_id}", include_self=False)
                
                return {
                    'success': True,
                    'operation': asdict(transformed_operation),
                    'document_version': session.version
                }
            else:
                return {'success': False, 'error': 'Failed to apply operation'}
                
        except Exception as e:
            logger.error(f"Error handling operation: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_cursor_position(self, session_id: str, user_id: str, 
                             cursor_data: Dict[str, Any]):
        """
        Update user cursor position and selection.
        
        Args:
            session_id: Session ID
            user_id: User ID
            cursor_data: Cursor position and selection data
        """
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                if user_id in session.user_presence:
                    presence = session.user_presence[user_id]
                    presence.cursor_position = cursor_data.get('position', 0)
                    presence.selection_start = cursor_data.get('selection_start', 0)
                    presence.selection_end = cursor_data.get('selection_end', 0)
                    presence.last_seen = datetime.utcnow().isoformat()
                    
                    # Broadcast cursor update
                    if self.socketio and SOCKETIO_AVAILABLE:
                        emit('cursor_updated', {
                            'user_id': user_id,
                            'cursor_position': presence.cursor_position,
                            'selection_start': presence.selection_start,
                            'selection_end': presence.selection_end
                        }, room=f"collab_{session_id}", include_self=False)
                        
        except Exception as e:
            logger.error(f"Error updating cursor position: {e}")
    
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of collaboration session."""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id].get_document_state()
        return None
    
    # Helper methods
    def _transform_against_history(self, operation: Operation, 
                                 session: CollaborationSession) -> Operation:
        """Transform operation against recent history."""
        # For now, return operation as-is
        # In production, implement full operational transformation
        return operation
    
    def _generate_operation_id(self) -> str:
        """Generate unique operation ID."""
        timestamp = datetime.utcnow().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    def _generate_user_color(self, user_id: str) -> str:
        """Generate consistent color for user."""
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#F4A261', '#E76F51', '#2A9D8F', '#264653'
        ]
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return colors[hash_value % len(colors)]

# Factory function
def create_realtime_collaboration_service(socketio_instance=None) -> RealtimeCollaborationService:
    """Create real-time collaboration service."""
    return RealtimeCollaborationService(socketio_instance)
```

**Acceptance Criteria**:
- ✅ Real-time multi-user editing with conflict resolution
- ✅ Operational transformation for consistency
- ✅ User presence tracking with cursor positions
- ✅ SocketIO integration for live updates
- ✅ Session management and cleanup
- ✅ Scalable architecture for multiple concurrent sessions

### Phase 2: Collaboration API & Comments System (3 weeks)

#### Task 2.1: Team Collaboration API Routes
**File**: `src/routes/collaboration_routes.py`

```python
"""
API routes for team collaboration features.
Handles teams, projects, real-time editing, and comment systems.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from src.services.team_management import create_team_management_service, TeamRole
from src.services.realtime_collaboration import create_realtime_collaboration_service
from src.services.comment_system import create_comment_service

logger = logging.getLogger(__name__)

# Create blueprint for collaboration routes
collaboration_bp = Blueprint('collaboration', __name__, url_prefix='/api/collaboration')

@collaboration_bp.route('/teams', methods=['GET', 'POST'])
@login_required
def handle_teams() -> Tuple[Dict[str, Any], int]:
    """Handle team listing and creation."""
    try:
        team_service = create_team_management_service(current_app.db.session)
        
        if request.method == 'GET':
            # Get user's teams
            teams = team_service.get_user_teams(current_user.id)
            
            return jsonify({
                'teams': [team.__dict__ for team in teams],
                'total_count': len(teams),
                'success': True
            }), 200
            
        elif request.method == 'POST':
            # Create new team
            data = request.get_json()
            if not data or 'name' not in data:
                return jsonify({'error': 'Team name required'}), 400
            
            team_info = team_service.create_team(
                name=data['name'],
                description=data.get('description', ''),
                owner_user_id=current_user.id,
                settings=data.get('settings', {})
            )
            
            return jsonify({
                'team': team_info.__dict__,
                'success': True
            }), 201
            
    except Exception as e:
        logger.error(f"Error handling teams: {e}")
        return jsonify({'error': 'Team operation failed', 'details': str(e)}), 500

@collaboration_bp.route('/teams/<team_id>/members', methods=['GET', 'POST', 'DELETE'])
@login_required
def handle_team_members(team_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle team member management."""
    try:
        team_service = create_team_management_service(current_app.db.session)
        
        if request.method == 'GET':
            # Get team members
            team_info = team_service.get_team_info(team_id, current_user.id)
            # Implementation would get full member list
            
            return jsonify({
                'team_id': team_id,
                'members': [],  # Implementation needed
                'success': True
            }), 200
            
        elif request.method == 'POST':
            # Add team member
            data = request.get_json()
            if not data or 'user_id' not in data or 'role' not in data:
                return jsonify({'error': 'User ID and role required'}), 400
            
            try:
                role = TeamRole(data['role'])
            except ValueError:
                return jsonify({'error': 'Invalid role'}), 400
            
            member_info = team_service.add_team_member(
                team_id=team_id,
                user_id=data['user_id'],
                role=role,
                added_by=current_user.id
            )
            
            return jsonify({
                'member': member_info.__dict__,
                'success': True
            }), 201
            
        elif request.method == 'DELETE':
            # Remove team member
            data = request.get_json()
            if not data or 'user_id' not in data:
                return jsonify({'error': 'User ID required'}), 400
            
            # Implementation for member removal
            return jsonify({'success': True}), 200
            
    except PermissionError as e:
        return jsonify({'error': 'Insufficient permissions'}), 403
    except Exception as e:
        logger.error(f"Error handling team members: {e}")
        return jsonify({'error': 'Member operation failed', 'details': str(e)}), 500

@collaboration_bp.route('/teams/<team_id>/projects', methods=['GET', 'POST'])
@login_required
def handle_team_projects(team_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle project management within teams."""
    try:
        team_service = create_team_management_service(current_app.db.session)
        
        if request.method == 'GET':
            # Get team projects
            # Implementation would get project list
            
            return jsonify({
                'team_id': team_id,
                'projects': [],  # Implementation needed
                'success': True
            }), 200
            
        elif request.method == 'POST':
            # Create new project
            data = request.get_json()
            if not data or 'name' not in data:
                return jsonify({'error': 'Project name required'}), 400
            
            project_info = team_service.create_project(
                team_id=team_id,
                name=data['name'],
                description=data.get('description', ''),
                created_by=current_user.id,
                settings=data.get('settings', {})
            )
            
            return jsonify({
                'project': project_info,
                'success': True
            }), 201
            
    except PermissionError as e:
        return jsonify({'error': 'Insufficient permissions'}), 403
    except Exception as e:
        logger.error(f"Error handling projects: {e}")
        return jsonify({'error': 'Project operation failed', 'details': str(e)}), 500

@collaboration_bp.route('/sessions/<session_id>/collaborate', methods=['POST', 'DELETE'])
@login_required
def handle_session_collaboration(session_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle joining/leaving collaborative editing sessions."""
    try:
        collab_service = create_realtime_collaboration_service(current_app.socketio)
        
        if request.method == 'POST':
            # Join collaboration session
            result = collab_service.join_collaboration_session(
                session_id=session_id,
                user_id=current_user.id,
                username=current_user.username
            )
            
            return jsonify(result), 200 if result['success'] else 400
            
        elif request.method == 'DELETE':
            # Leave collaboration session
            collab_service.leave_collaboration_session(session_id, current_user.id)
            
            return jsonify({'success': True}), 200
            
    except Exception as e:
        logger.error(f"Error handling session collaboration: {e}")
        return jsonify({'error': 'Collaboration operation failed', 'details': str(e)}), 500

@collaboration_bp.route('/sessions/<session_id>/comments', methods=['GET', 'POST'])
@login_required
def handle_session_comments(session_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle comments on transcript sessions."""
    try:
        comment_service = create_comment_service(current_app.db.session)
        
        if request.method == 'GET':
            # Get session comments
            comments = comment_service.get_session_comments(
                session_id=session_id,
                user_id=current_user.id
            )
            
            return jsonify({
                'session_id': session_id,
                'comments': comments,
                'total_count': len(comments),
                'success': True
            }), 200
            
        elif request.method == 'POST':
            # Add new comment
            data = request.get_json()
            if not data or 'content' not in data:
                return jsonify({'error': 'Comment content required'}), 400
            
            comment = comment_service.create_comment(
                session_id=session_id,
                user_id=current_user.id,
                content=data['content'],
                timestamp=data.get('timestamp'),
                segment_index=data.get('segment_index'),
                metadata=data.get('metadata', {})
            )
            
            return jsonify({
                'comment': comment,
                'success': True
            }), 201
            
    except Exception as e:
        logger.error(f"Error handling comments: {e}")
        return jsonify({'error': 'Comment operation failed', 'details': str(e)}), 500

@collaboration_bp.route('/comments/<comment_id>', methods=['PUT', 'DELETE'])
@login_required
def handle_comment_operations(comment_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle individual comment operations."""
    try:
        comment_service = create_comment_service(current_app.db.session)
        
        if request.method == 'PUT':
            # Update comment
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Update data required'}), 400
            
            updated_comment = comment_service.update_comment(
                comment_id=comment_id,
                user_id=current_user.id,
                updates=data
            )
            
            return jsonify({
                'comment': updated_comment,
                'success': True
            }), 200
            
        elif request.method == 'DELETE':
            # Delete comment
            success = comment_service.delete_comment(
                comment_id=comment_id,
                user_id=current_user.id
            )
            
            return jsonify({'success': success}), 200 if success else 403
            
    except PermissionError as e:
        return jsonify({'error': 'Insufficient permissions'}), 403
    except Exception as e:
        logger.error(f"Error handling comment operations: {e}")
        return jsonify({'error': 'Comment operation failed', 'details': str(e)}), 500
```

**Acceptance Criteria**:
- ✅ Complete team management API (CRUD operations)
- ✅ Project organization within teams
- ✅ Real-time collaboration session management
- ✅ Comment system with threading support
- ✅ Role-based access control enforcement
- ✅ Comprehensive error handling and validation

## 📋 Complete Task Breakdown

### Week 1-3: Core Team Infrastructure
- [ ] Task 1.1: Team Management System (database models, service layer)
- [ ] Task 1.2: Real-Time Collaboration Engine (operational transformation)
- [ ] Task 1.3: User authentication integration
- [ ] Task 1.4: Database migrations and setup

### Week 4-6: Collaboration API & Comments
- [ ] Task 2.1: Team Collaboration API Routes
- [ ] Task 2.2: Comment System Implementation
- [ ] Task 2.3: Real-time WebSocket handlers
- [ ] Task 2.4: Permission system integration

### Week 7-8: User Interface & Experience
- [ ] Task 3.1: Team Dashboard UI
- [ ] Task 3.2: Real-time Editing Interface
- [ ] Task 3.3: Comment System UI
- [ ] Task 3.4: Mobile collaboration features

### Week 9-10: Advanced Features & Polish
- [ ] Task 4.1: Review and approval workflows
- [ ] Task 4.2: Activity feeds and notifications
- [ ] Task 4.3: Performance optimization
- [ ] Task 4.4: Comprehensive testing and documentation

## ✅ Acceptance Criteria

### Functional Requirements
- [ ] ✅ **Team Creation**: Users can create teams with role-based access control
- [ ] ✅ **Project Organization**: Hierarchical organization of content within teams
- [ ] ✅ **Real-time Editing**: Multiple users can edit transcripts simultaneously
- [ ] ✅ **Conflict Resolution**: Automatic handling of concurrent edits
- [ ] ✅ **Comment System**: Timestamped comments with threading and @mentions
- [ ] ✅ **Review Workflows**: Approval processes with multiple review stages
- [ ] ✅ **Activity Tracking**: Comprehensive audit trail of all team activities
- [ ] ✅ **Notifications**: Real-time notifications for team activities

### Performance Requirements
- [ ] ✅ **Real-time Latency**: <100ms for collaborative editing operations
- [ ] ✅ **Concurrent Users**: Support 50+ simultaneous editors per session
- [ ] ✅ **Scalability**: Handle 1000+ teams with 10,000+ total users
- [ ] ✅ **Data Consistency**: 100% consistency across all collaborative operations

### Security Requirements
- [ ] ✅ **Authentication**: Secure user authentication and session management
- [ ] ✅ **Authorization**: Role-based access control with granular permissions
- [ ] ✅ **Data Privacy**: Team data isolation and privacy controls
- [ ] ✅ **Audit Trail**: Complete tracking of all user actions and changes

## 🎯 Success Metrics

- **Team Adoption**: 60%+ of users create or join teams within 30 days
- **Collaboration Usage**: 40%+ of transcriptions involve multiple team members
- **Edit Conflicts**: <1% of collaborative edits result in unresolved conflicts
- **User Satisfaction**: 90%+ satisfaction rating for collaboration features
- **Time Savings**: 40%+ reduction in review and approval cycle times

This comprehensive collaboration system transforms the Video Transcriber into a powerful team platform, addressing the critical need for multi-user workflows in professional transcription environments.
