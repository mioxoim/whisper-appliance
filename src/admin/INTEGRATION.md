"""
Integration Guide for New Admin Panel

To integrate the new modular admin panel, make these changes in main.py:

1. Replace the import:
   FROM: from modules import AdminPanel
   TO:   from admin import init_admin_panel

2. Replace admin panel initialization (around line 182-187):
   FROM:
   if WHISPER_AVAILABLE:
       admin_panel = AdminPanel(
           whisper_available=True, system_stats=system_stats, connected_clients=connected_clients, model=model
       )
   else:
       admin_panel = AdminPanel(WHISPER_AVAILABLE, system_stats, connected_clients, model_manager, chat_history)
   
   TO:
   # Initialize admin panel with new modular structure
   admin_panel = init_admin_panel(app, model_manager, system_stats)

3. Remove the old admin route (around line 1517-1520):
   DELETE:
   @app.route("/admin")
   def admin():
       """Admin panel with enhanced navigation"""
       return admin_panel.get_admin_interface()

   The new admin panel registers its own routes via Blueprint.

4. Update any references to admin_panel methods:
   - admin_panel.increment_transcription_count() remains the same
   - Other methods should work as before

5. Make sure psutil is installed for system monitoring:
   pip install psutil

The new admin panel provides:
- Modular CSS structure
- Separate JavaScript modules
- Template-based rendering
- Enhanced model management
- System monitoring
- Better organization
"""
