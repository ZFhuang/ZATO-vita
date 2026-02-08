import os
import re

# Get parent directory of script directory (project root)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Target file path
snow_path = os.path.join(base_dir, 'game', 'snowblossom.rpy')


def main():
    # Check if file exists
    if not os.path.exists(snow_path):
        print(f"File does not exist: {snow_path}")
        return False
    
    # Read original file
    with open(snow_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    modifications = []

    # 1. Reduce default particle count (50 -> 25)
    if 'max_particles=50' in content:
        content = content.replace('max_particles=50', 'max_particles=25')
        modifications.append("Default particle count: 50 -> 25")

    # 2. Reduce default depth levels (10 -> 5)
    if 'self.depth = kwargs.get("depth", 10)' in content:
        content = content.replace(
            'self.depth = kwargs.get("depth", 10)',
            'self.depth = kwargs.get("depth", 5)'
        )
        modifications.append("Default depth levels: 10 -> 5")

    # 3. Add screen size cache in __init__ (after self.image = self.image_init(image))
    old_image_init = "self.image = self.image_init(image)"
    new_image_init = """self.image = self.image_init(image)
            
            # PSVita optimization: cache screen size to avoid per-frame config access
            self.screen_width = renpy.config.screen_width
            self.screen_height = renpy.config.screen_height"""

    if old_image_init in content and 'self.screen_width' not in content:
        content = content.replace(old_image_init, new_image_init)
        modifications.append("Added screen size cache")

    # 4. Optimize particle generation in create method, use local variables
    old_create = """        def create(self, particles, st):
            \"\"\"
            This is internally called every frame by the Particles object to create new particles.
            We'll just create new particles if the number of particles on the screen is
            lower than the max number of particles we can have.
            \"\"\"
            if particles is None or len(particles) < self.max_particles:
                
                depth = random.randint(1, self.depth)
                
                depth_speed = 1.5-depth/(self.depth+0.0)
                
                return [ SnowParticle(self.image[depth-1],      
                                      random.uniform(-self.wind, self.wind)*depth_speed,  
                                      self.speed*depth_speed,  
                                      random.randint(self.xborder[0], self.xborder[1]), 
                                      random.randint(self.yborder[0], self.yborder[1]), 
                                      ) ]"""

    new_create = """        def create(self, particles, st):
            \"\"\"
            This is internally called every frame by the Particles object to create new particles.
            We'll just create new particles if the number of particles on the screen is
            lower than the max number we can have.
            \"\"\"
            if particles is None or len(particles) < self.max_particles:
                # PSVita optimization: use local variables to reduce attribute access
                max_p = self.max_particles
                depth_val = self.depth
                depth = random.randint(1, depth_val)
                depth_speed = 1.5 - depth / (depth_val + 0.0)
                
                return [ SnowParticle(self.image[depth-1],
                                      random.uniform(-self.wind, self.wind) * depth_speed,
                                      self.speed * depth_speed,
                                      random.randint(self.xborder[0], self.xborder[1]),
                                      random.randint(self.yborder[0], self.yborder[1]),
                                      ) ]"""

    if old_create in content:
        content = content.replace(old_create, new_create)
        modifications.append("Optimized create method (local variable caching)")

    # 5. Optimize screen boundary check in update method
    old_update = """        def update(self, st):
            \"\"\"
            Called internally in every frame to update the particle.
            \"\"\"
            
            
            if self.oldst is None:
                self.oldst = st
            
            lag = st - self.oldst
            self.oldst = st
            
            self.xpos += lag * self.wind
            self.ypos += lag * self.speed
            
            if self.ypos > renpy.config.screen_height or\\
            (self.wind< 0 and self.xpos < 0) or (self.wind > 0 and self.xpos > renpy.config.screen_width):
                    return None
            
            return int(self.xpos), int(self.ypos), st, self.image"""

    new_update = """        def update(self, st):
            \"\"\"
            Called internally in every frame to update the particle.
            \"\"\"
            # PSVita optimization: use factory cached screen size
            factory = self.factory
            
            if self.oldst is None:
                self.oldst = st
            
            lag = st - self.oldst
            self.oldst = st
            
            self.xpos += lag * self.wind
            self.ypos += lag * self.speed
            
            # Use cached screen size
            if self.ypos > factory.screen_height or \\
               (self.wind < 0 and self.xpos < 0) or \\
               (self.wind > 0 and self.xpos > factory.screen_width):
                return None
            
            return int(self.xpos), int(self.ypos), st, self.image"""

    if old_update in content and 'factory = self.factory' not in content:
        content = content.replace(old_update, new_update)
        modifications.append("Optimized update method (using cached screen size)")

    # 6. Modify SnowParticle constructor, add factory reference
    old_particle_init = """    class SnowParticle(object):
        \"\"\"
        Represents every particle in the screen.
        \"\"\"
        def __init__(self, image, wind, speed, xborder, yborder):
            \"\"\"
            Initializes the snow particle. This is called automatically when the object is created.
            \"\"\"
            
            self.image = image"""

    new_particle_init = """    class SnowParticle(object):
        \"\"\"
        Represents every particle in the screen.
        \"\"\"
        def __init__(self, factory, image, wind, speed, xborder, yborder):
            \"\"\"
            Initializes the snow particle. This is called automatically when the object is created.
            \"\"\"
            self.factory = factory  # PSVita optimization: cache factory reference
            self.image = image"""

    if old_particle_init in content and 'self.factory = factory' not in content:
        content = content.replace(old_particle_init, new_particle_init)
        modifications.append("Modified SnowParticle constructor, added factory parameter")

    # 7. Update particle creation call in create method, pass factory
    old_particle_create = """                return [ SnowParticle(self.image[depth-1],
                                      random.uniform(-self.wind, self.wind) * depth_speed,
                                      self.speed * depth_speed,
                                      random.randint(self.xborder[0], self.xborder[1]),
                                      random.randint(self.yborder[0], self.yborder[1]),
                                      ) ]"""

    new_particle_create = """                return [ SnowParticle(self, self.image[depth-1],
                                      random.uniform(-self.wind, self.wind) * depth_speed,
                                      self.speed * depth_speed,
                                      random.randint(self.xborder[0], self.xborder[1]),
                                      random.randint(self.yborder[0], self.yborder[1]),
                                      ) ]"""

    if old_particle_create in content and 'SnowParticle(self, self.image' not in content:
        content = content.replace(old_particle_create, new_particle_create)
        modifications.append("Updated particle creation call, passing factory reference")

    # Write back to file
    if content != original_content:
        with open(snow_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Optimized file: {snow_path}")
        print("Modifications:")
        for mod in modifications:
            print(f"  - {mod}")
        return True
    else:
        print(f"File already optimized or format mismatch, no changes needed: {snow_path}")
        return True  # Not an error, just no changes needed


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
