import 'package:english_words/english_words.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';


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
  
  List<AppItem> apps = [
    AppItem(name: 'Chrome', isEnabled: false),
    AppItem(name: 'Edge', isEnabled: true),
    AppItem(name: 'PyCharm', isEnabled: false),
    AppItem(name: 'Zoom', isEnabled: false),
  ];

  void enableAll() {
    for (var app in apps) {
      app.isEnabled = true;
    }
    notifyListeners();
  }

  void disableAll() {
    for (var app in apps) {
      app.isEnabled = false;
    }
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
    checkForAll(); // Check if we need to disable the lock button
    notifyListeners();
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
                // Left button (WiFi)
                ElevatedButton( 
                  onPressed: () {}, 
                  style: ElevatedButton.styleFrom( 
                    shape: CircleBorder(),
                    padding: EdgeInsets.all(20),
                    backgroundColor: Colors.blue, 
                    foregroundColor: Colors.black, 
                  ),
                  child: Icon(Icons.wifi, size: 30)
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
                  onPressed: () {}, 
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
