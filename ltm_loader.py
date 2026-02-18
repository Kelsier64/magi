import os
import frontmatter
from typing import List, Tuple
from models import ltm

def load_ltm_files(directory: str, agent_name: str) -> Tuple[List[ltm], List[ltm]]:
    """
    Loads LTM files from a directory, filtering by agent_name.
    
    Logic:
    - 'visible_to': list of agents who can SEE/KNOW this memory exists.
    - 'active_for': list of agents for whom this memory is currently ACTIVE/IN-CONTEXT.
    
    Returns tuple (active_ltm_list, visible_ltm_list)
    """
    active_ltm = []
    visible_ltm = []
    
    agent_name_lower = agent_name.lower()
    
    if not os.path.exists(directory):
        return active_ltm, visible_ltm
        
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            filepath = os.path.join(directory, filename)
            try:
                # python-frontmatter loads the file and parses YAML
                post = frontmatter.load(filepath)
                metadata = post.metadata
                content = post.content
                
                # Normalize lists to lowercase for comparison
                # Handle cases where metadata might be None or missing keys
                visible_to_raw = metadata.get('visible_to', [])
                if isinstance(visible_to_raw, str): # Handle single string case just in case
                     visible_to_raw = [visible_to_raw]
                visible_to = [str(x).lower() for x in visible_to_raw] if visible_to_raw else []

                active_for_raw = metadata.get('active_for', [])
                if isinstance(active_for_raw, str):
                     active_for_raw = [active_for_raw]
                active_for = [str(x).lower() for x in active_for_raw] if active_for_raw else []

                # Check visibility
                is_visible = False
                if not visible_to or 'all' in visible_to or agent_name_lower in visible_to:
                     is_visible = True
                
                # Check active
                is_active = False
                if not active_for or 'all' in active_for or agent_name_lower in active_for:
                    is_active = True
                
                if is_visible or is_active:
                     memory_name = metadata.get('name', filename)
                     description = metadata.get('description', '')
                     
                     memory = ltm(
                         name=memory_name,
                         description=description,
                         content=content,
                         path=filepath,
                         active_for=active_for,
                         visible_to=visible_to
                     )
                     
                     if is_active:
                         active_ltm.append(memory)
                     elif is_visible:
                         visible_ltm.append(memory)
                     
            except Exception as e:
                print(f"Error loading LTM file {filename}: {e}")
                
    return active_ltm, visible_ltm

if __name__ == "__main__":
    # Test
    test_dir = "./ltm"
    agent_name = "Magi-01"
    active, visible = load_ltm_files(test_dir, agent_name)
    print(f"Loaded for {agent_name}:")
    print(f"Active ({len(active)}): {[m.name for m in active]}")
    print(f"Visible ({len(visible)}): {[m.name for m in visible]}")
