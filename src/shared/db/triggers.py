class TriggersManager:
    @staticmethod
    def check_urls_count():
        return """
        CREATE OR REPLACE FUNCTION check_urls_count()
        RETURNS TRIGGER AS $$
        DECLARE
            max_links INTEGER := 100;
            current_count INTEGER;   
        BEGIN    
            SELECT COUNT(*) INTO current_count 
            FROM links 
            WHERE project_id = NEW.project_id AND is_active = TRUE;
            IF current_count >= max_links THEN
                RAISE EXCEPTION 'Maximum % links allowed per project. Current count: %, Project ID: %', 
                max_links, current_count, NEW.project_id;
            END IF;
    
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;"""

    @staticmethod
    def get_links_limit_trigger():
        return """
        CREATE TRIGGER links_limit_trigger
            BEFORE INSERT ON links
            FOR EACH ROW
            EXECUTE FUNCTION check_urls_count();
        """

    @staticmethod
    def get_roles_counter():
        return """
        CREATE OR REPLACE FUNCTION check_roles_counter()
        RETURNS TRIGGER AS $$
        DECLARE
            min_roles INTEGER := 1;
            current_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO current_count
            FROM roles
            WHERE project_id = OLD.project_id AND priority < 10;
            IF current_count <= min_roles THEN
                RAISE EXCEPTION 'Cannot delete role: minimum % roles with priority < 10 required per project. Project ID: %', 
                    min_roles, OLD.project_id;
            END IF;
            
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
        """

    @staticmethod
    def get_min_roles_limit():
        return """
        CREATE TRIGGER min_roles_limit
            BEFORE DELETE ON roles
            FOR EACH ROW
            EXECUTE FUNCTION check_roles_counter();
        """

    @staticmethod
    def get_protect_default_role_function():
        return """
        CREATE OR REPLACE FUNCTION protect_default_or_creator_role()
        RETURNS TRIGGER AS $$
        BEGIN
            IF EXISTS (SELECT 1 FROM projects WHERE default_role_id = OLD.id) THEN
                RAISE EXCEPTION 'Cannot delete default role. Role ID: % is used as default role', OLD.id;
            END IF;
            IF OLD.priority = 10 THEN
                RAISE EXCEPTION 'Cannot delete creator role. Role ID: % has priority 10', OLD.id;
            END IF;

            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
        """

    @staticmethod
    def get_protect_default_role_trigger():
        return """
        CREATE TRIGGER protect_default_role_trigger
            BEFORE DELETE ON roles
            FOR EACH ROW
            EXECUTE FUNCTION protect_default_or_creator_role();
        """

    @staticmethod
    def get_protect_important_roles_function():
        return """
        CREATE OR REPLACE FUNCTION protect_important_roles()
        RETURNS TRIGGER AS $$
        DECLARE
            is_default_role BOOLEAN;
        BEGIN
            IF OLD.priority = 10 THEN
                IF NEW.priority != OLD.priority OR
                   NEW.create_tasks != OLD.create_tasks OR
                   NEW.delete_tasks != OLD.delete_tasks OR
                   NEW.update_tasks != OLD.update_tasks OR
                   NEW.update_project != OLD.update_project OR
                   NEW.generate_url != OLD.generate_url OR
                   NEW.delete_users != OLD.delete_users OR
                   NEW.change_roles != OLD.change_roles OR
                   NEW.manage_links != OLD.manage_links THEN

                    RAISE EXCEPTION 'Cannot modify creator role. Only name can be changed. Role ID: %', NEW.id;
                END IF;
            END IF;

            SELECT EXISTS (
                SELECT 1 FROM projects 
                WHERE default_role_id = NEW.id
            ) INTO is_default_role;

            IF is_default_role THEN
                IF NEW.priority != OLD.priority OR
                   NEW.create_tasks != OLD.create_tasks OR
                   NEW.delete_tasks != OLD.delete_tasks OR
                   NEW.update_tasks != OLD.update_tasks OR
                   NEW.update_project != OLD.update_project OR
                   NEW.generate_url != OLD.generate_url OR
                   NEW.delete_users != OLD.delete_users OR
                   NEW.change_roles != OLD.change_roles OR
                   NEW.manage_links != OLD.manage_links THEN

                    RAISE EXCEPTION 'Cannot modify default role. All permissions and priority are protected. Role ID: %', NEW.id;
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """

    @staticmethod
    def get_protect_important_roles_triggers_on_update():
        return """
        CREATE TRIGGER protect_important_roles_update
            BEFORE UPDATE ON roles
            FOR EACH ROW
            EXECUTE FUNCTION protect_important_roles();
        """


