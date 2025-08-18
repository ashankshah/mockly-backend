# Frontend Credit Integration Guide for Mockly Interview Platform

## Overview
This guide provides comprehensive instructions for implementing credit functionality in the Mockly frontend application. The credit system ensures users must have sufficient credits to start interview sessions, with each session costing 1 credit. When users run out of credits, they cannot continue practicing until an administrator refills their account.

## Backend API Endpoints

### 1. Credit Management Endpoints

#### Get Credit Balance
```
GET /credits/balance
Authorization: Bearer {jwt_token}
Response: { credits: number, message: string }
```

#### Get Credit Transaction History
```
GET /credits/transactions?limit=20&offset=0
Authorization: Bearer {jwt_token}
Response: { transactions: Array, total_transactions: number }
```

#### Refund Credits (Admin Only)
```
POST /credits/refund
Authorization: Bearer {jwt_token}
Body: { amount: number, reason: string }
Response: { credits: number, message: string }
```

### 2. Session Eligibility Check
```
GET /check-session-eligibility
Authorization: Bearer {jwt_token}
Response: { 
  eligible: boolean, 
  reason: string, 
  credits: number, 
  required_credits: number 
}
```

### 3. Updated User Profile
```
GET /users/profile
Authorization: Bearer {jwt_token}
Response: { 
  user: User, 
  stats: UserStats, 
  recent_progress: Array, 
  starred_questions: Array,
  credits: number  // NEW FIELD
}
```

## Frontend Implementation Requirements

### 1. Credit Display Components

#### Credit Balance Widget
- **Location**: Header/Navigation bar, user profile page
- **Features**:
  - Display current credit balance prominently
  - Show credit icon (💰 or similar)
  - Update in real-time after transactions
  - Color-coded: Green (sufficient), Red (insufficient), Yellow (low)

#### Credit Status Display
- **Trigger**: Always visible when credits are low
- **Features**:
  - Clear indication of remaining credits
  - Warning message when credits are insufficient
  - Contact admin for credit refills
  - Real-time balance display

#### Credit Transaction History
- **Location**: User profile or dedicated credits page
- **Features**:
  - Paginated list of all credit transactions
  - Transaction type icons
  - Date and time stamps
  - Credit change indicators (+/-)
  - Running balance

### 2. Session Flow Integration

#### Pre-Session Credit Check
- **Implementation**: Before starting any interview session
- **Flow**:
  1. Call `/check-session-eligibility` endpoint
  2. If eligible: proceed with session
  3. If not eligible: show insufficient credits message
  4. Display current credit balance prominently
  5. Provide contact information for admin credit refills

#### Session Start Confirmation
- **Implementation**: When user clicks "Start Interview"
- **Features**:
  - Show credit deduction confirmation
  - Display remaining credits after deduction
  - Clear indication that 1 credit will be deducted

#### Credit Deduction Feedback
- **Implementation**: After successful session start
- **Features**:
  - Toast notification: "1 credit deducted. Remaining: X credits"
  - Update credit balance display
  - Option to view transaction in history

### 3. User Experience Enhancements

#### Low Credit Warnings
- **Triggers**: When credits ≤ 2
- **Features**:
  - Banner notification: "Low credits remaining"
  - Contact admin message prominently displayed
  - Warning in session start buttons
  - Clear indication of remaining sessions

#### Credit Status Indicators
- **Implementation**: Throughout the application
- **Features**:
  - Session buttons: Enabled/disabled based on credits
  - Credit balance in user dropdown
  - Visual indicators for credit status

#### Responsive Credit Updates
- **Implementation**: Real-time updates
- **Features**:
  - Update credit balance after each transaction
  - Refresh eligibility status
  - Optimistic UI updates with rollback on errors

### 4. Error Handling

#### Insufficient Credits Error (402)
- **Handling**: Graceful degradation
- **Features**:
  - Clear error message: "You need 1 credit to start a session"
  - Contact admin information for credit refills
  - Current balance display
  - Explanation of credit system

#### Network Errors
- **Handling**: Fallback behavior
- **Features**:
  - Retry mechanisms
  - Offline credit validation
  - User-friendly error messages

### 5. State Management

#### Credit State Structure
```typescript
interface CreditState {
  balance: number;
  isLoading: boolean;
  error: string | null;
  transactions: CreditTransaction[];
  lastUpdated: Date;
}
```

#### Credit Actions
```typescript
// Redux/Context actions
const creditActions = {
  fetchBalance: () => void;
  deductCredits: (amount: number) => Promise<void>;
  refreshTransactions: () => void;
  checkEligibility: () => Promise<boolean>;
};
```

### 6. UI Components Structure

#### Credit Components Hierarchy
```
src/
├── components/
│   ├── credits/
│   │   ├── CreditBalance.tsx
│   │   ├── CreditStatusDisplay.tsx
│   │   ├── CreditTransactionHistory.tsx
│   │   ├── CreditStatusIndicator.tsx
│   │   └── LowCreditWarning.tsx
│   ├── session/
│   │   ├── SessionCreditCheck.tsx
│   │   └── SessionStartButton.tsx
│   └── common/
│       └── CreditIcon.tsx
├── hooks/
│   ├── useCredits.ts
│   ├── useCreditEligibility.ts
│   └── useCreditTransactions.ts
├── services/
│   └── creditService.ts
└── types/
    └── credits.ts
```

### 7. Implementation Steps

#### Phase 1: Core Credit Display
1. Create credit balance component
2. Integrate with user profile
3. Add credit display to header
4. Implement basic credit fetching

#### Phase 2: Session Integration
1. Add credit check to session start
2. Implement credit deduction flow
3. Add eligibility validation
4. Update session buttons

#### Phase 3: Credit Management
1. Create credit status display components
2. Implement admin credit refill flow
3. Add transaction history
4. Handle credit validation errors

#### Phase 4: Enhanced UX
1. Add low credit warnings
2. Implement real-time updates
3. Add credit status indicators
4. Optimize error handling

### 8. Testing Requirements

#### Unit Tests
- Credit balance calculations
- Transaction processing
- Eligibility validation
- Error handling

#### Integration Tests
- Credit API endpoints
- Session flow with credits
- Credit validation flow
- Real-time updates

#### User Acceptance Tests
- Credit deduction flow
- Credit validation experience
- Low credit scenarios
- Error recovery

### 9. Performance Considerations

#### Optimization Strategies
- Cache credit balance locally
- Debounce credit updates
- Lazy load transaction history
- Optimistic UI updates

#### Monitoring
- Credit API response times
- Transaction success rates
- User credit usage patterns
- Error frequency

### 10. Security Considerations

#### Client-Side Validation
- Validate credit amounts before submission
- Prevent negative credit inputs
- Sanitize user inputs

#### Server-Side Validation
- Always verify credits on backend
- Prevent credit manipulation
- Audit all credit transactions

## Example Implementation

### Credit Balance Component
```typescript
import React from 'react';
import { useCredits } from '../hooks/useCredits';

export const CreditBalance: React.FC = () => {
  const { balance, isLoading, error } = useCredits();
  
  if (isLoading) return <div>Loading credits...</div>;
  if (error) return <div>Error loading credits</div>;
  
  const getCreditColor = (credits: number) => {
    if (credits <= 1) return 'text-red-500';
    if (credits <= 3) return 'text-yellow-500';
    return 'text-green-500';
  };
  
  return (
    <div className="flex items-center space-x-2">
      <span className="text-lg">💰</span>
      <span className={`font-bold ${getCreditColor(balance)}`}>
        {balance} credits
      </span>
    </div>
  );
};
```

### Session Start Button with Credit Check
```typescript
import React from 'react';
import { useCreditEligibility } from '../hooks/useCreditEligibility';

export const SessionStartButton: React.FC<{ onStart: () => void }> = ({ onStart }) => {
  const { eligible, credits, checkEligibility } = useCreditEligibility();
  
  const handleClick = async () => {
    const canStart = await checkEligibility();
    if (canStart) {
      onStart();
    } else {
      // Show credit purchase modal
    }
  };
  
  return (
    <button
      onClick={handleClick}
      disabled={!eligible}
      className={`px-6 py-3 rounded-lg font-semibold ${
        eligible 
          ? 'bg-blue-500 hover:bg-blue-600 text-white' 
          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
      }`}
    >
      {eligible ? 'Start Interview' : `Need 1 Credit (${credits} remaining)`}
    </button>
  );
};
```

## Conclusion

This credit system provides a controlled access model while maintaining excellent user experience. The implementation should prioritize:

1. **Clear Communication**: Users should always know their credit status
2. **Seamless Integration**: Credits should not disrupt the interview flow
3. **Admin Control**: Credit refills managed by administrators
4. **Transparent Tracking**: Users should see all credit transactions
5. **Graceful Degradation**: Handle errors and edge cases smoothly

The system is designed to be simple and focused on preventing users from continuing when they run out of credits. Future enhancements can include automated credit refills, referral bonuses, or subscription models as needed.
