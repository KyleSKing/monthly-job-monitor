//
//  ScoreFilterView.swift
//  JobMonitorApp
//
//  Created by Job Monitor on iOS
//

import SwiftUI

struct ScoreFilterView: View {
    @Binding var minScore: Int
    
    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Text("Minimum Score: \(minScore)")
                    .font(.headline)
                Spacer()
            }
            
            HStack {
                Text("0")
                Slider(value: Binding(
                    get: { Double(minScore) },
                    set: { minScore = Int($0.rounded()) }
                ), in: 0...10, step: 1)
                Text("10")
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(10)
        .shadow(radius: 2)
    }
}

#Preview {
    ScoreFilterView(minScore: .constant(7))
}