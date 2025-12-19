import { useEffect, useRef, useState } from 'react';

const MUSIC_TRACKS = [
  '/assets/music/track1.mp3',
  '/assets/music/track2.mp3',
  '/assets/music/track3.mp3',
  '/assets/music/track4.mp3',
  '/assets/music/track5.mp3',
  '/assets/music/track6.mp3',
  '/assets/music/track7.mp3',
];

// Fonction pour obtenir un index aléatoire différent du précédent
const getRandomTrackIndex = (currentIndex: number, totalTracks: number): number => {
  if (totalTracks <= 1) return 0;
  
  let newIndex;
  do {
    newIndex = Math.floor(Math.random() * totalTracks);
  } while (newIndex === currentIndex);
  
  return newIndex;
};

export const useMusicPlayer = () => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [currentTrackIndex, setCurrentTrackIndex] = useState(() => 
    Math.floor(Math.random() * MUSIC_TRACKS.length) // Démarrage aléatoire
  );
  const [isMuted, setIsMuted] = useState(() => {
    // Récupérer la préférence depuis localStorage
    const saved = localStorage.getItem('musicMuted');
    return saved === 'true';
  });

  useEffect(() => {
    // Créer l'élément audio
    audioRef.current = new Audio(MUSIC_TRACKS[currentTrackIndex]);
    audioRef.current.volume = 0.3; // Volume à 30%
    audioRef.current.muted = isMuted;

    // Événement pour passer au morceau suivant (ALÉATOIRE)
    const handleEnded = () => {
      setCurrentTrackIndex((prev) => getRandomTrackIndex(prev, MUSIC_TRACKS.length));
    };

    audioRef.current.addEventListener('ended', handleEnded);

    // Démarrer la lecture
    if (!isMuted) {
      audioRef.current.play().catch(() => {
        // Autoplay bloqué par le navigateur (normal au premier chargement)
      });
    }

    // Nettoyage
    return () => {
      if (audioRef.current) {
        audioRef.current.removeEventListener('ended', handleEnded);
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [currentTrackIndex, isMuted]);

  const toggleMute = () => {
    setIsMuted((prev) => {
      const newMuted = !prev;
      localStorage.setItem('musicMuted', String(newMuted));
      
      if (audioRef.current) {
        audioRef.current.muted = newMuted;
        if (!newMuted) {
          audioRef.current.play().catch(() => {
            // Lecture bloquée par le navigateur
          });
        }
      }
      
      return newMuted;
    });
  };

  return {
    isMuted,
    toggleMute,
    currentTrack: MUSIC_TRACKS[currentTrackIndex],
  };
};
