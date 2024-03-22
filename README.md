<h1>SonoShare</h1> 
SonoShare - A Cross-Platform Playlist Conversion Web Application

Team member - Isaac Ajifowobaje (full stack developer)

<h3>Technologies</h3>
	
Backend: Python (Django), MySQL
		An alternative is NodeJs but Django has batteries included aiding faster deployment
	Frontend: HTML, CSS, JavaScript (React)
	Server: Linux
	Web-Server: Nginx
	API Integration: Spotify API, Apple Music API, and others as needed.


1. <h3>Introduction and Challenge</h3>
	
 	Problem Statement: Music lovers currently have difficulty sharing playlists with others who use a different music platform. The inability to seamlessly transfer playlists between services causes frustration and limits music discovery.
	
 	Proposed Solution: SonoShare will be a user-friendly web application that allows playlist sharing across popular music streaming platforms.
	
 	Project Significance: SonoShare aims to enhance music experiences by removing barriers between platforms, increasing user satisfaction, and promoting the sharing of musical preferences.
	
 	This project will be free and have not payment integrations


3. <h3>Existing Solutions</h3> Tools like SongShift, Soundiiz and  anniemusic exist but have their strengths and imitations.

	SongShifts is a native app and downloading adds an extra step. It is also only available on iOS
	Soundiiz is a web app that does most things right. However the UI could be more intuitive
	Anniemusic only handles song conversations and not playlists

	Technical Approaches: Research algorithms and techniques employed for song matching between music services, including metadata analysis and potential use of audio fingerprinting.


4. <h3>Risks</h3>
	API Considerations: music service APIs (Spotify, Apple Music, etc.), available endpoints and potential rate limits.
Security Considerations: Auth0 would be employed to ensure secure access for users.


4. <h3>Project Objectives</h3>
	
 	Core Functionality:
		Enable users to input playlist links from supported music streaming services.
		Develop a robust song matching mechanism for high-accuracy playlist conversion.
		Allow users to select their desired output music platform.
		Construct and display the converted playlist on the chosen service.
	
 	Additional Features (Potential):
		Social sharing integration to streamline playlist sharing within the app.
		Rudimentary analytics to track conversion statistics for users.


5. <h3>Infrastructure</h3>
	
 	Deployment Strategy: Continuous Deployment
	Deployment Platform: Heroku: Beginner-friendly, integrates well with Python apps.
		An alternative is AWS (Elastic Beanstalk): More scalable, but has more moving parts. We want to deploy quickly, get the product to users so to test and iterate.

	Version Control Connection: Git repository link to Heroku
Automation: Platform automatically deploy updates from the main branch whenever new code is pushed



