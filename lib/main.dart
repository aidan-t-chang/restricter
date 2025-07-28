import 'package:english_words/english_words.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

class AppItem {
  String name;
  bool isEnabled;
  AppItem({required this.name, required this.isEnabled});
}

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (context) => MyAppState(),
      child: MaterialApp(
        title: 'Namer App',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color.fromARGB(255, 53, 106, 252)),
        ),
        home: MyHomePage(),
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

  void toggleLock() {
    isLocked = !isLocked;
    for (var app in apps) {
      app.isEnabled = true;
    }
    notifyListeners();
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
                    appState.toggleLock();
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
