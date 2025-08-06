import 'package:english_words/english_words.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:firebase_database/firebase_database.dart';


class AppItem {
  String name;
  bool isEnabled;
  AppItem({required this.name, required this.isEnabled});
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (context) => MyAppState(),
      child: MaterialApp(
        title: 'Restricter App',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color.fromARGB(255, 53, 106, 252)),
        ),
        home: AuthWrapper(),
      ),
    );
  }
}

class MyAppState extends ChangeNotifier {
  var current = WordPair.random();
  var isLocked = false;
  final DatabaseReference _database = FirebaseDatabase.instance.ref();
  String? _connectedDesktopId;
  
  List<AppItem> apps = [
    AppItem(name: 'Chrome', isEnabled: false),
    AppItem(name: 'Edge', isEnabled: true),
    AppItem(name: 'PyCharm', isEnabled: false),
    AppItem(name: 'Zoom', isEnabled: false),
  ];

  String? get connectedDesktopId => _connectedDesktopId;

  void enableAll() {
    for (var app in apps) {
      app.isEnabled = true;
    }
    _sendCommandToDesktop('enable_all');
    notifyListeners();
  }

  void disableAll() {
    for (var app in apps) {
      app.isEnabled = false;
    }
    _sendCommandToDesktop('disable_all');
    notifyListeners();
  }

  void checkForAll() {
    for (var app in apps) {
      if (app.isEnabled == false) {
        isLocked = false;
        return; // Exit early if any app is disabled
      } 
    }
  }

  void getNext() {
    current = WordPair.random();
    notifyListeners();
  }

  void toggleLockState() {
    isLocked = !isLocked;
    if (isLocked) {
      // When locking, enable all apps
      enableAll();
    } else {
      // When unlocking, disable all apps
      disableAll();
    }
  }

  void toggleApp(int index) {
    apps[index].isEnabled = !apps[index].isEnabled;
    
    // Send command to desktop
    _sendCommandToDesktop('toggle_app', params: {
      'app_name': apps[index].name,
      'enabled': apps[index].isEnabled
    });
    
    checkForAll(); // Check if we need to disable the lock button
    notifyListeners();
  }

  // Connect a desktop machine to this user
  Future<void> connectDesktop(String desktopId, String desktopName) async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return;

    try {
      await _database
          .child('desktop_connections')
          .child(user.uid)
          .child(desktopId)
          .set({
        'connected': true,
        'last_seen': ServerValue.timestamp,
        'desktop_name': desktopName,
      });
      
      _connectedDesktopId = desktopId;
      notifyListeners();
    } catch (e) {
      print('Error connecting desktop: $e');
    }
  }

  // Send command to connected desktop
  Future<void> _sendCommandToDesktop(String action, {Map<String, dynamic>? params}) async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null || _connectedDesktopId == null) return;

    try {
      await _database
          .child('commands')
          .child(user.uid)
          .push()
          .set({
        'action': action,
        'timestamp': ServerValue.timestamp,
        'desktop_id': _connectedDesktopId,
        'params': params ?? {},
      });
    } catch (e) {
      print('Error sending command: $e');
    }
  }

  // Disconnect desktop
  Future<void> disconnectDesktop() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null || _connectedDesktopId == null) return;

    try {
      await _database
          .child('desktop_connections')
          .child(user.uid)
          .child(_connectedDesktopId!)
          .update({
        'connected': false,
        'last_seen': ServerValue.timestamp,
      });
      
      _connectedDesktopId = null;
      notifyListeners();
    } catch (e) {
      print('Error disconnecting desktop: $e');
    }
  }
}

class MyHomePage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    var appState = context.watch<MyAppState>();

    return Scaffold(
      appBar: AppBar(
        title: Text('Restricter'),
        actions: [
          IconButton(
            icon: Icon(Icons.logout),
            onPressed: () async {
              await FirebaseAuth.instance.signOut();
            },
          ),
        ],
        backgroundColor: Colors.blue,
      ),
      body: Column(
        children: [
          // Top buttons row
          Padding(
            padding: const EdgeInsets.only(top: 60),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Left button (Connection Status)
                ElevatedButton( 
                  onPressed: () {
                    _showDesktopConnectionDialog(context, appState);
                  }, 
                  style: ElevatedButton.styleFrom( 
                    shape: CircleBorder(),
                    padding: EdgeInsets.all(20),
                    backgroundColor: appState.connectedDesktopId != null ? Colors.green : Colors.red, 
                    foregroundColor: Colors.black, 
                  ),
                  child: Icon(Icons.computer, size: 30)
                ),
                SizedBox(width: 20),
                // Center button (Lock)
                ElevatedButton( 
                  onPressed: () {
                    appState.toggleLockState();
                  }, 
                  style: ElevatedButton.styleFrom( 
                    shape: CircleBorder(),
                    padding: EdgeInsets.all(30),
                    backgroundColor: appState.isLocked ? Colors.red : Colors.green, 
                    foregroundColor: Colors.black, 
                  ),
                  child: Icon(appState.isLocked ? Icons.lock_outline : Icons.lock_open, size: 40)
                ),
                SizedBox(width: 20),
                // Right button (Settings)
                ElevatedButton( 
                  onPressed: () {
                    _showDesktopConnectionDialog(context, appState);
                  }, 
                  style: ElevatedButton.styleFrom( 
                    shape: CircleBorder(),
                    padding: EdgeInsets.all(20),
                    backgroundColor: Colors.grey, 
                    foregroundColor: Colors.black, 
                  ),
                  child: Icon(Icons.settings, size: 30)
                ),
              ],
            ),
          ),
          SizedBox(height: 40),
          // Apps list
          Expanded(
            child: ListView.builder(
              itemCount: appState.apps.length,
              itemBuilder: (context, index) {
                return AppRow(
                  app: appState.apps[index],
                  onToggle: () => appState.toggleApp(index),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  void _showDesktopConnectionDialog(BuildContext context, MyAppState appState) {
    final TextEditingController desktopIdController = TextEditingController();
    final TextEditingController desktopNameController = TextEditingController();

    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text(appState.connectedDesktopId == null 
            ? 'Connect Desktop' 
            : 'Desktop Connection'),
          content: appState.connectedDesktopId == null
            ? Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'To connect your desktop:',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  SizedBox(height: 12),
                  Text('1. Install and run the Restricter desktop app'),
                  Text('2. Find your Desktop ID in the app window'),
                  Text('3. Copy the 8-character ID (e.g., A1B2C3D4)'),
                  Text('4. Enter the ID and name below'),
                  SizedBox(height: 20),
                  Container(
                    padding: EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.blue.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.blue.shade200),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.info, color: Colors.blue, size: 20),
                        SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Desktop ID is displayed in your Restricter desktop application',
                            style: TextStyle(fontSize: 12, color: Colors.blue.shade700),
                          ),
                        ),
                      ],
                    ),
                  ),
                  SizedBox(height: 16),
                  TextField(
                    controller: desktopIdController,
                    decoration: InputDecoration(
                      labelText: 'Desktop ID',
                      hintText: 'e.g., A1B2C3D4',
                      border: OutlineInputBorder(),
                      helperText: 'Found in your desktop Restricter app',
                    ),
                    textCapitalization: TextCapitalization.characters,
                    maxLength: 12,
                  ),
                  SizedBox(height: 10),
                  TextField(
                    controller: desktopNameController,
                    decoration: InputDecoration(
                      labelText: 'Desktop Name',
                      hintText: 'e.g., My Work Computer',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ],
              )
            : Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.computer, color: Colors.green, size: 48),
                  SizedBox(height: 16),
                  Text(
                    'Connected to:',
                    style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                  ),
                  Text(
                    '${appState.connectedDesktopId}',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 8),
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.green.shade100,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      'Status: Connected',
                      style: TextStyle(color: Colors.green.shade700, fontSize: 12),
                    ),
                  ),
                ],
              ),
          actions: [
            if (appState.connectedDesktopId != null)
              TextButton(
                onPressed: () {
                  appState.disconnectDesktop();
                  Navigator.of(context).pop();
                },
                child: Text('Disconnect', style: TextStyle(color: Colors.red)),
              ),
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text('Cancel'),
            ),
            if (appState.connectedDesktopId == null)
              ElevatedButton(
                onPressed: () {
                  if (desktopIdController.text.isNotEmpty && 
                      desktopNameController.text.isNotEmpty) {
                    appState.connectDesktop(
                      desktopIdController.text.trim().toUpperCase(),
                      desktopNameController.text.trim(),
                    );
                    Navigator.of(context).pop();
                  }
                },
                child: Text('Connect'),
              ),
          ],
        );
      },
    );
  }
}

class AppRow extends StatelessWidget {
  final AppItem app;
  final VoidCallback onToggle;

  const AppRow({
    super.key,
    required this.app,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: EdgeInsets.symmetric(vertical: 8),
      padding: EdgeInsets.symmetric(horizontal: 20, vertical: 2),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(6),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.2),
            spreadRadius: 1,
            blurRadius: 3,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            app.name,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          Switch(
            value: app.isEnabled,
            onChanged: (value) => onToggle(),
            activeColor: Colors.red,
            inactiveThumbColor: Colors.grey,
            inactiveTrackColor: Colors.grey.withOpacity(0.3),
          ),
        ],
      ),
    );
  }
}

// Authentication wrapper to handle login/logout states
class AuthWrapper extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return StreamBuilder<User?>(
      stream: FirebaseAuth.instance.authStateChanges(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        
        if (snapshot.hasData) {
          // User is logged in
          return MyHomePage();
        } else {
          // User is not logged in
          return LoginPage();
        }
      },
    );
  }
}

// Simple login page
class LoginPage extends StatefulWidget {
  @override
  _LoginPageState createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  String _errorMessage = '';

  Future<void> _signIn() async {
    setState(() {
      _isLoading = true;
      _errorMessage = '';
    });

    try {
      await FirebaseAuth.instance.signInWithEmailAndPassword(
        email: _emailController.text.trim(),
        password: _passwordController.text.trim(),
      );
    } on FirebaseAuthException catch (e) {
      setState(() {
        _errorMessage = e.message ?? 'An error occurred';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _signUp() async {
    setState(() {
      _isLoading = true;
      _errorMessage = '';
    });

    try {
      await FirebaseAuth.instance.createUserWithEmailAndPassword(
        email: _emailController.text.trim(),
        password: _passwordController.text.trim(),
      );
    } on FirebaseAuthException catch (e) {
      setState(() {
        _errorMessage = e.message ?? 'An error occurred';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _signInWithGoogle() async {
    setState(() {
      _isLoading = true;
      _errorMessage = '';
    });

    try {
      // Trigger the authentication flow
      final GoogleSignInAccount? googleUser = await GoogleSignIn().signIn();
      
      if (googleUser == null) {
        // User canceled the sign-in
        setState(() {
          _isLoading = false;
        });
        return;
      }

      // Obtain the auth details from the request
      final GoogleSignInAuthentication googleAuth = await googleUser.authentication;

      // Create a new credential
      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      // Once signed in, return the UserCredential
      await FirebaseAuth.instance.signInWithCredential(credential);
    } on FirebaseAuthException catch (e) {
      setState(() {
        _errorMessage = e.message ?? 'An error occurred';
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to sign in with Google: ${e.toString()}';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Login'),
        backgroundColor: Colors.blue,
      ),
      body: Padding(
        padding: EdgeInsets.all(20),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _emailController,
              decoration: InputDecoration(
                labelText: 'Email',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.emailAddress,
            ),
            SizedBox(height: 20),
            TextField(
              controller: _passwordController,
              decoration: InputDecoration(
                labelText: 'Password',
                border: OutlineInputBorder(),
              ),
              obscureText: true,
            ),
            SizedBox(height: 20),
            if (_errorMessage.isNotEmpty)
              Text(
                _errorMessage,
                style: TextStyle(color: Colors.red),
              ),
            SizedBox(height: 20),
            _isLoading
                ? CircularProgressIndicator()
                : Column(
                    children: [
                      ElevatedButton(
                        onPressed: _signIn,
                        style: ElevatedButton.styleFrom(
                          minimumSize: Size(double.infinity, 50),
                        ),
                        child: Text('Sign In'),
                      ),
                      SizedBox(height: 10),
                      ElevatedButton(
                        onPressed: _signUp,
                        style: ElevatedButton.styleFrom(
                          minimumSize: Size(double.infinity, 50),
                          backgroundColor: Colors.green,
                        ),
                        child: Text('Sign Up'),
                      ),
                      SizedBox(height: 10),
                      ElevatedButton.icon(
                        onPressed: _signInWithGoogle,
                        style: ElevatedButton.styleFrom(
                          minimumSize: Size(double.infinity, 50),
                          backgroundColor: Colors.white,
                          foregroundColor: Colors.black,
                          side: BorderSide(color: Colors.grey),
                        ),
                        label: Text('Sign in with Google'),
                      ),
                    ],
                  ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }
}
