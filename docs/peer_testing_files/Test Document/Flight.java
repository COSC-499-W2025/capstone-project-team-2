// File: Flight.java   Author: Alan Kennedy   Date: Jan. 14, 2013
// Description: This class represents a generic flight object, which stores data
//              that describes a the flight.

public class Flight {
   protected String departLocation,  // Departure Airport
                    destination,     // Destination Airport
                    flightNumber;    // Flight number, e.g. CS006, CS078, or CS388
   protected Time departTime,        // Time of departure (Time object)
                  duration;          // Duration of flight (Time object)

   private static int count = 1;

   public Flight(String dl, String dest, Time dt, Time dur) {
      departLocation = dl;
      destination = dest;
      departTime = dt;
      duration = dur;
      setFlightNumber();
      count = (count+1)%1000;
   }

   // This method uses that private static variable count to set flightNumber to a String
   // value of this form "CSxxx", where CS indicates the airlines, and xxx is the 3-digit
   // number. Note that the three digit number can have leading zeros.
   private void setFlightNumber() {
      String fill="";
      if(count<10) fill="00";
      else if(count<100) fill="0";
      flightNumber = "CS" + fill + count;
   }

   // Accessor Methods
   public String getDepartLocation() { return departLocation; }
   public String getDestination() { return destination; }
   public String getFlightNumber() { return flightNumber; }
   public Time getDepartTime() { return departTime; }
   public Time getDuration() { return duration; }

   // Mutator Methods
   public void setDepartTime(Time t) { departTime = t; }
   public void setDuration(Time t) { duration = t; }

   public String toString() {
      return "\nFlight " + flightNumber + " departs " + departLocation + " for " +
             destination + " at " + departTime + "\n" ;
   }
}
      


