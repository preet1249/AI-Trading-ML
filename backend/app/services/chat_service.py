"""
Chat Service - MongoDB-based chat history management
- Create chats
- Save messages
- Load chat history
- Delete chats
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid

from app.db.mongodb_client import get_mongodb

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat history in MongoDB"""

    @classmethod
    async def create_chat(
        cls,
        user_id: str,
        title: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create a new chat

        Args:
            user_id: User ID
            title: Optional chat title (auto-generated if not provided)

        Returns:
            Tuple (success, message, chat_id)
        """
        try:
            mongodb = get_mongodb()
            chats_collection = mongodb.get_collection("chats")

            chat_id = str(uuid.uuid4())

            chat_doc = {
                "_id": chat_id,
                "user_id": user_id,
                "title": title or "New Chat",
                "messages": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True
            }

            await chats_collection.insert_one(chat_doc)

            logger.info(f"✅ Chat created: {chat_id} for user {user_id}")
            return True, "Chat created", chat_id

        except Exception as e:
            logger.error(f"Error creating chat: {e}")
            return False, "Failed to create chat", None

    @classmethod
    async def save_message(
        cls,
        chat_id: str,
        user_id: str,
        user_message: str,
        ai_response: Dict,
        prediction_data: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Save a message exchange to a chat

        Args:
            chat_id: Chat ID
            user_id: User ID
            user_message: User's message
            ai_response: AI's response
            prediction_data: Optional prediction data

        Returns:
            Tuple (success, message)
        """
        try:
            mongodb = get_mongodb()
            chats_collection = mongodb.get_collection("chats")

            # Verify chat belongs to user
            chat = await chats_collection.find_one({
                "_id": chat_id,
                "user_id": user_id
            })

            if not chat:
                return False, "Chat not found or access denied"

            # Create message objects
            user_msg = {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.utcnow()
            }

            ai_msg = {
                "role": "assistant",
                "content": ai_response.get("content", ""),
                "prediction": prediction_data,
                "timestamp": datetime.utcnow()
            }

            # Auto-generate title from first message if needed
            update_data = {
                "$push": {
                    "messages": {
                        "$each": [user_msg, ai_msg]
                    }
                },
                "$set": {
                    "updated_at": datetime.utcnow()
                }
            }

            # If this is the first message, set title from user message
            if not chat.get("messages") and chat.get("title") == "New Chat":
                # Use first 50 chars of message as title
                title = user_message[:50] + ("..." if len(user_message) > 50 else "")
                update_data["$set"]["title"] = title

            await chats_collection.update_one(
                {"_id": chat_id},
                update_data
            )

            logger.info(f"✅ Message saved to chat: {chat_id}")
            return True, "Message saved"

        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return False, "Failed to save message"

    @classmethod
    async def get_user_chats(
        cls,
        user_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get all chats for a user

        Args:
            user_id: User ID
            limit: Max chats to return

        Returns:
            List of chat metadata (without full messages)
        """
        try:
            mongodb = get_mongodb()
            chats_collection = mongodb.get_collection("chats")

            chats = await chats_collection.find(
                {"user_id": user_id, "is_active": True},
                {"messages": 0}  # Exclude messages for performance
            ).sort("updated_at", -1).limit(limit).to_list(length=limit)

            # Convert datetime to ISO string for JSON serialization
            for chat in chats:
                chat["id"] = chat.pop("_id")
                chat["created_at"] = chat["created_at"].isoformat()
                chat["updated_at"] = chat["updated_at"].isoformat()

            return chats

        except Exception as e:
            logger.error(f"Error getting user chats: {e}")
            return []

    @classmethod
    async def get_chat_by_id(
        cls,
        chat_id: str,
        user_id: str
    ) -> Optional[Dict]:
        """
        Get a specific chat with all messages

        Args:
            chat_id: Chat ID
            user_id: User ID

        Returns:
            Full chat dict or None
        """
        try:
            mongodb = get_mongodb()
            chats_collection = mongodb.get_collection("chats")

            chat = await chats_collection.find_one({
                "_id": chat_id,
                "user_id": user_id,
                "is_active": True
            })

            if not chat:
                return None

            # Convert datetime to ISO string
            chat["id"] = chat.pop("_id")
            chat["created_at"] = chat["created_at"].isoformat()
            chat["updated_at"] = chat["updated_at"].isoformat()

            # Convert message timestamps
            for msg in chat.get("messages", []):
                if "timestamp" in msg:
                    msg["timestamp"] = msg["timestamp"].isoformat()

            return chat

        except Exception as e:
            logger.error(f"Error getting chat: {e}")
            return None

    @classmethod
    async def delete_chat(
        cls,
        chat_id: str,
        user_id: str
    ) -> Tuple[bool, str]:
        """
        Delete a chat (soft delete)

        Args:
            chat_id: Chat ID
            user_id: User ID

        Returns:
            Tuple (success, message)
        """
        try:
            mongodb = get_mongodb()
            chats_collection = mongodb.get_collection("chats")

            result = await chats_collection.update_one(
                {"_id": chat_id, "user_id": user_id},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )

            if result.modified_count == 0:
                return False, "Chat not found or already deleted"

            logger.info(f"✅ Chat deleted: {chat_id}")
            return True, "Chat deleted"

        except Exception as e:
            logger.error(f"Error deleting chat: {e}")
            return False, "Failed to delete chat"

    @classmethod
    async def update_chat_title(
        cls,
        chat_id: str,
        user_id: str,
        title: str
    ) -> Tuple[bool, str]:
        """
        Update chat title

        Args:
            chat_id: Chat ID
            user_id: User ID
            title: New title

        Returns:
            Tuple (success, message)
        """
        try:
            mongodb = get_mongodb()
            chats_collection = mongodb.get_collection("chats")

            result = await chats_collection.update_one(
                {"_id": chat_id, "user_id": user_id, "is_active": True},
                {"$set": {"title": title, "updated_at": datetime.utcnow()}}
            )

            if result.modified_count == 0:
                return False, "Chat not found"

            logger.info(f"✅ Chat title updated: {chat_id}")
            return True, "Title updated"

        except Exception as e:
            logger.error(f"Error updating chat title: {e}")
            return False, "Failed to update title"


# Singleton instance
chat_service = ChatService()
