"""
Adaptateur Supabase pour remplacer SQLAlchemy.
Fournit une interface similaire à SQLAlchemy mais utilise l'API REST Supabase.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Generic
from supabase import Client

from app.core.supabase_client import get_supabase_client

T = TypeVar('T')


class SupabaseDB:
    """
    Adaptateur de base de données utilisant Supabase API.
    Remplace SQLAlchemy Session.
    """
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()
    
    def query(self, model_class: type) -> 'SupabaseQuery':
        """Crée une requête pour un modèle donné."""
        return SupabaseQuery(self.client, model_class)
    
    def add(self, instance: Any) -> None:
        """Ajoute une instance (pour compatibilité SQLAlchemy, utilise upsert)."""
        self.merge(instance)
    
    def merge(self, instance: Any) -> None:
        """Fait un upsert (insert ou update) d'une instance."""
        table_name = instance.__class__.__tablename__
        data = self._instance_to_dict(instance)
        
        # Supabase upsert nécessite que la clé primaire soit présente
        # Si elle n'est pas présente, on fait un insert
        primary_key = self._get_primary_key(instance)
        if primary_key not in data or data[primary_key] is None:
            # Insert simple
            self.client.table(table_name).insert(data).execute()
        else:
            # Upsert (insert ou update basé sur la clé primaire)
            self.client.table(table_name).upsert(data).execute()
    
    def delete(self, instance: Any) -> None:
        """Supprime une instance."""
        table_name = instance.__class__.__tablename__
        primary_key = self._get_primary_key(instance)
        primary_key_value = getattr(instance, primary_key)
        
        self.client.table(table_name).delete().eq(primary_key, primary_key_value).execute()
    
    def commit(self) -> None:
        """Commit (pour compatibilité SQLAlchemy, ne fait rien car Supabase commit automatiquement)."""
        pass
    
    def flush(self) -> None:
        """Flush (pour compatibilité SQLAlchemy, ne fait rien car Supabase commit automatiquement)."""
        pass
    
    def rollback(self) -> None:
        """Rollback (pour compatibilité SQLAlchemy, non supporté par Supabase)."""
        # Supabase commit automatiquement, on ne peut pas rollback
        pass
    
    def close(self) -> None:
        """Ferme la connexion (pour compatibilité SQLAlchemy)."""
        pass
    
    def expire_all(self) -> None:
        """Expire tous les objets (pour compatibilité SQLAlchemy)."""
        pass
    
    def __enter__(self):
        """Support du context manager (with statement)."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support du context manager (with statement)."""
        self.close()
        return False  # Ne pas supprimer l'exception si elle existe
    
    def _instance_to_dict(self, instance: Any) -> Dict[str, Any]:
        """Convertit une instance de modèle en dictionnaire."""
        import uuid as uuid_module
        data = {}
        for column in instance.__table__.columns:
            value = getattr(instance, column.name, None)
            
            # Convertir les dates/datetime en ISO string pour Supabase
            if isinstance(value, datetime):
                value = value.isoformat()
            elif hasattr(value, 'isoformat'):  # Pour date aussi
                value = value.isoformat()
            # Convertir les UUID en string pour JSON
            elif isinstance(value, uuid_module.UUID):
                value = str(value)
            
            # Convertir les valeurs None - Supabase accepte None
            # Mais pour les champs required, on ne devrait pas avoir None
            data[column.name] = value
        return data
    
    def _get_primary_key(self, instance: Any) -> str:
        """Récupère le nom de la clé primaire d'un modèle."""
        for column in instance.__table__.columns:
            if column.primary_key:
                return column.name
        raise ValueError(f"No primary key found for {instance.__class__.__name__}")


class SupabaseQuery:
    """Requête Supabase similaire à SQLAlchemy Query."""
    
    def __init__(self, client: Client, model_class: type):
        self.client = client
        self.model_class = model_class
        self.table_name = model_class.__tablename__
        # Toujours démarrer avec un select(*) pour obtenir un builder exécutable
        self.query = client.table(self.table_name).select("*")
        self._filters = []
        self._limit_value = None
        self._offset_value = None
    
    def filter(self, *criteria) -> 'SupabaseQuery':
        """Ajoute un filtre à la requête."""
        # Support pour les filtres SQLAlchemy de base
        for criterion in criteria:
            # Gérer les différents types de critères SQLAlchemy
            if hasattr(criterion, '__class__'):
                criterion_class_name = criterion.__class__.__name__
                
                # BinaryExpression (Column == value, Column != value, etc.)
                if criterion_class_name == 'BinaryExpression':
                    left = criterion.left
                    right = criterion.right
                    op = criterion.operator
                    
                    # Extraire le nom de la colonne
                    if hasattr(left, 'key'):
                        column_name = left.key
                    elif hasattr(left, 'name'):
                        column_name = left.name
                    elif hasattr(left, '__str__'):
                        # Pour les cas comme Column('org_id'), extraire le nom
                        column_str = str(left)
                        # Si c'est une chaîne simple, l'utiliser directement
                        if '.' not in column_str and '(' not in column_str:
                            column_name = column_str
                        else:
                            # Extraire le nom de colonne d'une expression
                            column_name = left.key if hasattr(left, 'key') else str(left)
                    else:
                        column_name = str(left)
                    
                    # Extraire la valeur
                    if hasattr(right, 'value'):
                        value = right.value
                    elif hasattr(right, 'element'):
                        value = right.element
                    elif hasattr(right, '__str__'):
                        # Pour les valeurs simples
                        value = right
                    else:
                        value = right
                    
                    # Convertir datetime en ISO string pour Supabase
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    # Pour les entiers (timestamps), s'assurer qu'ils restent des entiers
                    # Supabase peut comparer les bigint correctement avec des entiers Python
                    elif isinstance(value, (int, float)) and not isinstance(value, bool):
                        # Garder les entiers comme entiers pour les comparaisons numériques
                        if isinstance(value, float) and value.is_integer():
                            value = int(value)
                        # Sinon, garder tel quel (int reste int, float reste float)
                    
                    # Appliquer l'opérateur
                    if op == 'eq' or str(op) == '==' or str(op).endswith('.eq'):
                        self.query = self.query.eq(column_name, value)
                    elif op == 'ne' or str(op) == '!=' or str(op).endswith('.ne'):
                        self.query = self.query.neq(column_name, value)
                    elif op == 'gt' or str(op) == '>' or str(op).endswith('.gt'):
                        self.query = self.query.gt(column_name, value)
                    elif op == 'ge' or str(op) == '>=' or str(op).endswith('.ge'):
                        self.query = self.query.gte(column_name, value)
                    elif op == 'lt' or str(op) == '<' or str(op).endswith('.lt'):
                        self.query = self.query.lt(column_name, value)
                    elif op == 'le' or str(op) == '<=' or str(op).endswith('.le'):
                        self.query = self.query.lte(column_name, value)
                    elif op == 'like' or str(op).endswith('.like'):
                        self.query = self.query.like(column_name, f"%{value}%")
                    elif op == 'ilike' or str(op).endswith('.ilike'):
                        self.query = self.query.ilike(column_name, f"%{value}%")
                    # Ajouter d'autres opérateurs si nécessaire
        return self
    
    def filter_by(self, **kwargs) -> 'SupabaseQuery':
        """Filtre par arguments nommés."""
        for key, value in kwargs.items():
            self.query = self.query.eq(key, value)
        return self
    
    def limit(self, limit: int) -> 'SupabaseQuery':
        """Limite le nombre de résultats."""
        self._limit_value = limit
        return self
    
    def offset(self, offset: int) -> 'SupabaseQuery':
        """Définit l'offset."""
        self._offset_value = offset
        return self
    
    def order_by(self, *columns) -> 'SupabaseQuery':
        """Trie les résultats."""
        for column in columns:
            # Gérer les différents types de colonnes SQLAlchemy
            is_desc = False
            column_name = None
            
            # Vérifier si c'est un UnaryExpression (desc() ou asc())
            if hasattr(column, '__class__'):
                if column.__class__.__name__ == 'UnaryExpression':
                    # C'est un desc() ou asc()
                    element = column.element
                    # Vérifier le modifier pour déterminer si c'est desc
                    if hasattr(column, 'modifier'):
                        modifier_str = str(column.modifier)
                        is_desc = 'DESC' in modifier_str or 'desc' in modifier_str.lower()
                    
                    if hasattr(element, 'key'):
                        column_name = element.key
                    elif hasattr(element, 'name'):
                        column_name = element.name
                    else:
                        column_name = str(element)
                else:
                    # Colonne normale
                    if hasattr(column, 'key'):
                        column_name = column.key
                    elif hasattr(column, 'name'):
                        column_name = column.name
                    else:
                        column_name = str(column)
            
            if column_name:
                # Supabase order() accepte desc comme paramètre
                # Format: .order(column_name, desc=True)
                if is_desc:
                    self.query = self.query.order(column_name, desc=True)
                else:
                    self.query = self.query.order(column_name)
        return self
    
    def all(self) -> List[Any]:
        """Retourne tous les résultats."""
        query = self.query
        
        # Appliquer limit et offset avec range pour Supabase
        if self._limit_value is not None or self._offset_value is not None:
            start = self._offset_value or 0
            end = start + (self._limit_value or 1000) - 1
            query = query.range(start, end)
        elif self._limit_value:
            query = query.limit(self._limit_value)
        
        response = query.execute()
        return [self._dict_to_instance(row) for row in response.data]
    
    def first(self) -> Optional[Any]:
        """Retourne le premier résultat."""
        results = self.limit(1).all()
        return results[0] if results else None
    
    def count(self) -> int:
        """Compte le nombre de résultats."""
        # Supabase ne supporte pas count directement, on récupère tous les résultats
        # Pour l'optimisation, on pourrait utiliser une fonction Supabase personnalisée
        response = self.query.execute()
        return len(response.data)
    
    def distinct(self) -> 'SupabaseQuery':
        """Ajoute DISTINCT à la requête (non supporté directement par Supabase, mais on peut filtrer)."""
        # Supabase ne supporte pas DISTINCT directement
        # On peut utiliser select() avec des colonnes spécifiques
        return self
    
    def _dict_to_instance(self, data: Dict[str, Any]) -> Any:
        """Convertit un dictionnaire en instance de modèle."""
        import uuid as uuid_module
        instance = self.model_class()
        # Si le modèle a __table__, utiliser les colonnes de la table
        if hasattr(instance, '__table__'):
            for column in instance.__table__.columns:
                if column.name in data:
                    value = data[column.name]
                    # Convertir les types si nécessaire
                    if value is not None:
                        try:
                            # Gérer les types SQLAlchemy
                            if hasattr(column.type, 'python_type'):
                                python_type = column.type.python_type
                                
                                # Gérer les dates/datetime
                                if python_type == datetime:
                                    if isinstance(value, str):
                                        # Parser la date ISO depuis Supabase
                                        try:
                                            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                        except:
                                            pass
                                
                                # Gérer les UUID (Supabase retourne des strings)
                                elif (python_type == uuid_module.UUID or 
                                      (hasattr(column.type, 'as_uuid') and column.type.as_uuid) or
                                      str(column.type).startswith('UUID')):
                                    if isinstance(value, str):
                                        try:
                                            value = uuid_module.UUID(value)
                                        except (ValueError, TypeError):
                                            pass
                                
                                # Convertir en type Python si nécessaire
                                if not isinstance(value, python_type):
                                    try:
                                        value = python_type(value)
                                    except (ValueError, TypeError):
                                        pass
                        except (ValueError, TypeError, AttributeError):
                            pass
                    setattr(instance, column.name, value)
        else:
            # Sinon, utiliser directement les attributs du dictionnaire
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
        return instance


def get_db():
    """Générateur de session Supabase (compatible avec FastAPI Depends)."""
    db = SupabaseDB()
    try:
        yield db
    finally:
        db.close()

