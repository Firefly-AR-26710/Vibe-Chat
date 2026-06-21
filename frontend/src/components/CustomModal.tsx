"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, X } from 'lucide-react';

interface CustomModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  content: string;
}

export const CustomModal: React.FC<CustomModalProps> = ({ 
  isOpen, 
  onClose, 
  title = "提示", 
  content 
}) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-slate-900/20 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className="relative w-full max-w-sm bg-white/90 backdrop-blur-xl border border-white/40 shadow-2xl rounded-3xl p-6 overflow-hidden"
          >
            {/* Dreamy bg */}
            <div className="absolute top-[-50px] right-[-50px] w-[150px] h-[150px] bg-rose-100 rounded-full blur-3xl opacity-60 pointer-events-none" />
            <div className="absolute bottom-[-50px] left-[-50px] w-[150px] h-[150px] bg-indigo-100 rounded-full blur-3xl opacity-60 pointer-events-none" />
            
            <div className="relative z-10 flex flex-col items-center text-center">
              <div className="w-12 h-12 rounded-full bg-rose-50 flex items-center justify-center mb-4 text-rose-500 shadow-sm border border-rose-100">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold text-slate-800 mb-2">{title}</h3>
              <p className="text-sm text-slate-500 mb-6 leading-relaxed">
                {content}
              </p>
              <button 
                onClick={onClose}
                className="w-full py-3 bg-gradient-to-r from-rose-400 to-rose-500 text-white rounded-xl font-medium shadow-md shadow-rose-200 hover:shadow-lg hover:shadow-rose-300 transition-all active:scale-95"
              >
                我知道了
              </button>
            </div>
            
            <button 
              onClick={onClose}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition-colors z-10"
            >
              <X className="w-5 h-5" />
            </button>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
