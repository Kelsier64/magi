import os
import frontmatter
from typing import List, Tuple
from models import ltm

def load_ltm_files(directory: str) -> List[ltm]:
    """
    Loads all LTM files from a directory.
    
    Returns a list of ltm objects.
    """
    all_ltms = []
    
    if not os.path.exists(directory):
        return all_ltms
        
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".md"):
            filepath = os.path.join(directory, filename)
            try:
                # python-frontmatter loads the file and parses YAML
                post = frontmatter.load(filepath)
                metadata = post.metadata
                content = post.content
                
                # Normalize lists to lowercase for comparison
                visible_to_raw = metadata.get('visible_to', [])
                if isinstance(visible_to_raw, str):
                     visible_to_raw = [visible_to_raw]
                visible_to = [str(x).lower() for x in visible_to_raw] if visible_to_raw else []

                active_for_raw = metadata.get('active_for', [])
                if isinstance(active_for_raw, str):
                     active_for_raw = [active_for_raw]
                active_for = [str(x).lower() for x in active_for_raw] if active_for_raw else []

                except_for_raw = metadata.get('except_for', [])
                if isinstance(except_for_raw, str):
                     except_for_raw = [except_for_raw]
                except_for = [str(x).lower() for x in except_for_raw] if except_for_raw else []

                memory_name = metadata.get('name', filename)
                description = metadata.get('description', '')
                
                memory = ltm(
                    name=memory_name,
                    description=description,
                    content=content,
                    path=filepath,
                    active_for=active_for,
                    visible_to=visible_to,
                    except_for=except_for
                )
                
                all_ltms.append(memory)
                     
            except Exception as e:
                print(f"Error loading LTM file {filename}: {e}")
                
    return all_ltms

def update_ltm_metadata(memory_name: str, agent_name: str, field: str, action: str = "add") -> str:
    """
    Updates the metadata of an LTM file.
    
    Args:
        memory_name (str): The name of the memory (filename without .md or 'name' in frontmatter).
        agent_name (str): The name of the agent.
        field (str): 'active_for' or 'visible_to'.
        action (str): 'add' or 'remove'.
    """
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ltm")
    target_file = None
    
    # Find the file
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            try:
                filepath = os.path.join(directory, filename)
                post = frontmatter.load(filepath)
                if post.metadata.get('name') == memory_name or filename == f"{memory_name}.md":
                    target_file = filepath
                    break
            except:
                continue
                
    if not target_file:
        return f"Memory '{memory_name}' not found."

    try:
        post = frontmatter.load(target_file)
        current_list = post.metadata.get(field, [])
        if isinstance(current_list, str):
            current_list = [current_list]
        
        if current_list is None:
            current_list = []
        
        # Ensure list
        current_list = list(current_list)
        
        if action == "add":
            if agent_name not in current_list:
                current_list.append(agent_name)
        elif action == "remove":
            if agent_name in current_list:
                current_list.remove(agent_name)
        
        # Add a newline at the end if it's missing (common issue with frontmatter)
        if not post.content.endswith('\n'):
             post.content += '\n'

        post.metadata[field] = current_list
        
        # Write back
        # frontmatter.dump uses UTF-8 by default
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        
        return f"Successfully updated {memory_name}"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error updating metadata: {e}"

if __name__ == "__main__":
   test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ltm")
   test = load_ltm_files(test_dir)
   for t in test:
       print(t.name,t.visible_to,t.active_for, t.except_for)
