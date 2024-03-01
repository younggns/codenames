import os
os.environ['OPENAI_API_KEY'] = 'Your OPENAI_API_KEY'

from chatarena.arena import Arena


arena = Arena.from_config("examples/codenames.json")
# Run the game for 10 steps
arena.run(num_steps=10)
arena.launch_cli()

# Alternatively, you can run your own main loop
for _ in range(10):
    arena.step()
    # Your code goes here ...